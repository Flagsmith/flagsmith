import typing
from collections.abc import Sequence

from common.core.utils import using_database_replica
from django.db import transaction
from django.db.models import Prefetch, Q, QuerySet
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from core.dataclasses import AuthorData
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState, FeatureStateValue
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.versioning.dataclasses import (
    EnvironmentDefaultChangeSet,
    EnvironmentMultivariateValueChangeSet,
    FeatureValue,
    FlagChangeSetOptionA,
    FlagChangeSetOptionB,
    KeyedMultivariateOptionChangeSet,
    MultivariateKeyValueChangeSet,
    MultivariateOptionUpdateChangeSet,
    MultivariateValueChangeSet,
    NewMultivariateOptionChangeSet,
    SegmentMultivariateValueChangeSet,
)
from features.versioning.exceptions import DirectFeatureStateWriteNotAllowedError
from features.versioning.models import EnvironmentFeatureVersion


def require_direct_state_write(
    environment: Environment, *, is_identity_override: bool
) -> None:
    if is_identity_override or not environment.use_v2_feature_versioning:
        return
    raise DirectFeatureStateWriteNotAllowedError()


def require_direct_state_write_for_state(feature_state: FeatureState) -> None:
    # FS rows attached to an unpublished EFV are a draft, so direct mutation is
    # part of the versioning flow rather than a bypass of it.
    efv = feature_state.environment_feature_version
    if efv is not None and not efv.published:
        return
    require_direct_state_write(
        environment=feature_state.environment,  # type: ignore[arg-type]
        is_identity_override=feature_state.identity_id is not None,
    )


def get_environment_flags_queryset(
    environment: Environment,
    feature_name: str = None,  # type: ignore[assignment]
) -> QuerySet[FeatureState]:
    """
    Get a queryset of the latest live versions of an environments' feature states
    """
    feature_states_list = get_environment_flags_list(environment, feature_name)
    return FeatureState.objects.filter(id__in=[fs.id for fs in feature_states_list])  # type: ignore[no-any-return]


def get_environment_flags_list(
    environment: Environment,
    feature_name: str | None = None,
    additional_filters: Q = None,  # type: ignore[assignment]
    additional_select_related_args: typing.Iterable[str] = None,  # type: ignore[assignment]
    additional_prefetch_related_args: typing.Iterable[
        typing.Union[str, Prefetch[typing.Any]]
    ] = None,  # type: ignore[assignment]
    from_replica: bool = False,
) -> list[FeatureState]:
    """
    Get a list of the latest committed versions of FeatureState objects that are
    associated with the given environment. Can be filtered to remove segment /
    identity overrides using additional_filters argument.

    Note: uses a single query to get all valid versions of a given environment's
    feature states. The logic to grab the latest version is then handled in python
    by building a dictionary. Returns a list of FeatureState objects.
    """
    return list(
        get_environment_flags_dict(
            environment,
            feature_name,
            additional_filters,
            additional_select_related_args,
            additional_prefetch_related_args,
            from_replica=from_replica,
        ).values()
    )


def get_environment_flags_dict(
    environment: Environment,
    feature_name: str | None = None,
    additional_filters: Q = None,  # type: ignore[assignment]
    additional_select_related_args: typing.Iterable[str] = None,  # type: ignore[assignment]
    additional_prefetch_related_args: typing.Iterable[
        typing.Union[str, Prefetch[typing.Any]]
    ] = None,  # type: ignore[assignment]
    key_function: typing.Callable[[FeatureState], tuple] = None,  # type: ignore[type-arg,assignment]
    from_replica: bool = False,
) -> dict[tuple | str | int, FeatureState]:  # type: ignore[type-arg]
    key_function = key_function or _get_distinct_key  # type: ignore[truthy-function]

    feature_states = _get_feature_states_queryset(
        environment,
        feature_name,
        additional_filters,
        additional_select_related_args,
        additional_prefetch_related_args,
        from_replica=from_replica,
    )

    # Build up a dictionary keyed off the relevant unique attributes as defined
    # by the provided key function and only keep the highest priority feature state
    # for each feature.
    feature_states_dict = {}  # type: ignore[var-annotated]
    for feature_state in feature_states:
        key = key_function(feature_state)
        current_feature_state = feature_states_dict.get(key)
        if not current_feature_state or feature_state > current_feature_state:
            feature_states_dict[key] = feature_state

    return feature_states_dict  # type: ignore[return-value]


def get_current_live_environment_feature_version(
    environment_id: int, feature_id: int
) -> EnvironmentFeatureVersion | None:
    return (  # type: ignore[no-any-return]
        EnvironmentFeatureVersion.objects.filter(
            environment_id=environment_id,
            feature_id=feature_id,
            published_at__isnull=False,
            live_from__lte=timezone.now(),
        )
        .order_by("-live_from")
        .first()
    )


def update_flag_option_a(
    environment: Environment, feature: Feature, change_set: FlagChangeSetOptionA
) -> FeatureState:
    with transaction.atomic():
        if environment.use_v2_feature_versioning:
            return _update_flag_option_a_for_versioning_v2(
                environment, feature, change_set
            )
        else:
            return _update_flag_option_a_for_versioning_v1(
                environment, feature, change_set
            )


def _update_flag_option_a_for_versioning_v2(
    environment: Environment, feature: Feature, change_set: FlagChangeSetOptionA
) -> FeatureState:
    from features.models import FeatureSegment, FeatureState

    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment,
        feature=feature,
        created_by=change_set.author.user,
        created_by_api_key=change_set.author.api_key,
    )

    if change_set.segment_id is not None:
        # Segment override - may or may not exist
        try:
            target_feature_state: FeatureState = new_version.feature_states.get(
                feature_segment__segment_id=change_set.segment_id,
            )
        except FeatureState.DoesNotExist:
            feature_segment = FeatureSegment.objects.create(
                feature=feature,
                segment_id=change_set.segment_id,
                environment=environment,
                environment_feature_version=new_version,
            )

            enabled, inherited_value = _resolve_new_override_inheritance(
                change_set.enabled,
                change_set.value,
                lambda: new_version.feature_states.get(
                    feature_segment__isnull=True, identity_id=None
                ),
            )
            target_feature_state = FeatureState.objects.create(
                feature=feature,
                environment=environment,
                feature_segment=feature_segment,
                environment_feature_version=new_version,
                enabled=enabled,
            )
            if inherited_value is not None:
                target_feature_state.feature_state_value.copy_from(inherited_value)
    else:
        # Environment default - always exists
        target_feature_state = new_version.feature_states.get(
            feature_segment__isnull=True,
            identity_id=None,
        )

    if change_set.enabled is not None:
        target_feature_state.enabled = change_set.enabled
        target_feature_state.save()

    if change_set.value is not None:
        _update_feature_state_value(
            target_feature_state.feature_state_value, change_set.value
        )

    if change_set.segment_id is not None:
        update_multivariate_values(target_feature_state, change_set.multivariate_values)
    else:
        update_environment_multivariate_options(
            target_feature_state, feature, change_set.environment_multivariate_values
        )

    if change_set.segment_id is not None and change_set.segment_priority is not None:
        _update_segment_priority(target_feature_state, change_set.segment_priority)

    new_version.publish(
        published_by=change_set.author.user,
        published_by_api_key=change_set.author.api_key,
    )

    return target_feature_state


def _update_flag_option_a_for_versioning_v1(
    environment: Environment, feature: Feature, change_set: FlagChangeSetOptionA
) -> FeatureState:
    from features.models import FeatureSegment, FeatureState

    if change_set.segment_id is not None:
        additional_filters = Q(feature_segment__segment_id=change_set.segment_id)
    else:
        additional_filters = Q(feature_segment__isnull=True, identity_id__isnull=True)

    latest_feature_states = get_environment_flags_dict(
        environment=environment,
        feature_name=feature.name,
        additional_filters=additional_filters,
    )

    if len(latest_feature_states) == 0 and change_set.segment_id is not None:
        feature_segment = FeatureSegment.objects.create(
            feature=feature,
            segment_id=change_set.segment_id,
            environment=environment,
        )

        enabled, inherited_value = _resolve_new_override_inheritance(
            change_set.enabled,
            change_set.value,
            lambda: _get_environment_default_feature_state(environment, feature),
        )
        target_feature_state: FeatureState = FeatureState.objects.create(
            feature=feature,
            environment=environment,
            feature_segment=feature_segment,
            enabled=enabled,
        )
        if inherited_value is not None:
            target_feature_state.feature_state_value.copy_from(inherited_value)
    else:
        assert len(latest_feature_states) == 1
        target_feature_state = list(latest_feature_states.values())[0]
        if change_set.enabled is not None:
            target_feature_state.enabled = change_set.enabled
            target_feature_state.save()

    if change_set.value is not None:
        _update_feature_state_value(
            target_feature_state.feature_state_value, change_set.value
        )

    if change_set.segment_id is not None:
        update_multivariate_values(target_feature_state, change_set.multivariate_values)
    else:
        update_environment_multivariate_options(
            target_feature_state, feature, change_set.environment_multivariate_values
        )

    if change_set.segment_id is not None and change_set.segment_priority is not None:
        _update_segment_priority(target_feature_state, change_set.segment_priority)

    return target_feature_state


def _get_environment_default_feature_state(
    environment: Environment, feature: Feature
) -> FeatureState:
    environment_default_states = get_environment_flags_dict(
        environment=environment,
        feature_name=feature.name,
        additional_filters=Q(feature_segment__isnull=True, identity_id__isnull=True),
    )
    assert len(environment_default_states) == 1
    return list(environment_default_states.values())[0]


def _resolve_new_override_inheritance(
    enabled: bool | None,
    value: FeatureValue | None,
    get_environment_default: typing.Callable[[], FeatureState],
) -> tuple[bool, FeatureStateValue | None]:
    """
    Resolve a new segment override's enabled flag and, when its value is
    omitted, the environment default FeatureStateValue to copy it from.
    """
    if enabled is not None and value is not None:
        return enabled, None
    environment_default = get_environment_default()
    return (
        enabled if enabled is not None else environment_default.enabled,
        environment_default.feature_state_value if value is None else None,
    )


def _update_feature_state_value(fsv: FeatureStateValue, value: FeatureValue) -> None:
    fsv.set_value(value.value, value.type_)
    fsv.save()


def update_multivariate_values(
    feature_state: FeatureState,
    values: Sequence[SegmentMultivariateValueChangeSet] | None,
) -> None:
    if values is None:
        return

    keys = {
        value.key
        for value in values
        if isinstance(value, MultivariateKeyValueChangeSet)
    }
    option_id_by_key: dict[str, int] = {}
    if keys:
        option_id_by_key = {
            key: option_id
            for key, option_id in MultivariateFeatureOption.objects.filter(
                feature_id=feature_state.feature_id, key__in=keys
            ).values_list("key", "id")
            if key is not None
        }
        if unknown_keys := keys - option_id_by_key.keys():
            raise ValidationError(
                f"Multivariate keys {sorted(unknown_keys)} do not belong to the feature"
            )
    resolved_values = [
        value
        if isinstance(value, MultivariateValueChangeSet)
        else MultivariateValueChangeSet(
            multivariate_feature_option_id=option_id_by_key[value.key],
            percentage_allocation=value.percentage_allocation,
        )
        for value in values
    ]

    existing = {
        mv.multivariate_feature_option_id: mv
        for mv in feature_state.multivariate_feature_state_values.all()
    }

    passed_option_ids = {
        value.multivariate_feature_option_id for value in resolved_values
    }
    effective_total = sum(
        value.percentage_allocation for value in resolved_values
    ) + sum(
        mv.percentage_allocation
        for option_id, mv in existing.items()
        if option_id not in passed_option_ids
    )
    if effective_total > 100:
        raise ValidationError(
            "Multivariate allocations for the feature state must not exceed "
            f"100%, got {effective_total}%."
        )

    for value in resolved_values:
        mv = existing.get(value.multivariate_feature_option_id)
        if mv is None:
            MultivariateFeatureStateValue.objects.create(
                feature_state=feature_state,
                multivariate_feature_option_id=value.multivariate_feature_option_id,
                percentage_allocation=value.percentage_allocation,
            )
        elif mv.percentage_allocation != value.percentage_allocation:
            mv.percentage_allocation = value.percentage_allocation
            mv.save()


def update_environment_multivariate_options(
    feature_state: FeatureState,
    feature: Feature,
    values: list[EnvironmentMultivariateValueChangeSet] | None,
) -> None:
    """
    Reconcile the feature's multivariate options with the given absolute list,
    then re-weight the given environment default feature state accordingly.
    """
    if values is None:
        return

    listed_option_ids = {
        value.multivariate_feature_option_id
        for value in values
        if isinstance(value, MultivariateOptionUpdateChangeSet)
    }
    listed_keys = {
        value.key
        for value in values
        if isinstance(value, KeyedMultivariateOptionChangeSet)
    }
    # Instance-level deletes so django-lifecycle hooks fire
    for option in feature.multivariate_options.all():
        if option.id in listed_option_ids or option.key in listed_keys:
            continue
        option.delete()

    reweighted_values = []
    for value in values:
        if isinstance(value, NewMultivariateOptionChangeSet):
            option = MultivariateFeatureOption(
                feature=feature,
                default_percentage_allocation=value.percentage_allocation,
            )
            option.set_value(value.value.value, value.value.type_)
            option.save()
        elif isinstance(value, KeyedMultivariateOptionChangeSet):
            option = _upsert_multivariate_option_by_key(feature, value)
        else:
            option = feature.multivariate_options.get(
                id=value.multivariate_feature_option_id
            )
            option.default_percentage_allocation = value.percentage_allocation
            if value.value is not None:
                option.set_value(value.value.value, value.value.type_)
            option.save()
        reweighted_values.append(
            MultivariateValueChangeSet(
                multivariate_feature_option_id=option.id,
                percentage_allocation=value.percentage_allocation,
            )
        )

    update_multivariate_values(feature_state, reweighted_values)


def _upsert_multivariate_option_by_key(
    feature: Feature,
    value: KeyedMultivariateOptionChangeSet,
) -> MultivariateFeatureOption:
    try:
        option = feature.multivariate_options.get(key=value.key)
    except MultivariateFeatureOption.DoesNotExist:
        if value.value is None:
            raise ValidationError("A new multivariate option requires a 'value'.")
        option = MultivariateFeatureOption(
            feature=feature,
            key=value.key,
            default_percentage_allocation=value.percentage_allocation,
        )
        option.set_value(value.value.value, value.value.type_)
        option.save()
        return option
    option.default_percentage_allocation = value.percentage_allocation
    if value.value is not None:
        option.set_value(value.value.value, value.value.type_)
    option.save()
    return option


def _create_segment_override(
    feature: Feature,
    environment: Environment,
    segment_id: int,
    enabled: bool,
    priority: int | None,
    version: EnvironmentFeatureVersion | None = None,
) -> FeatureState:
    from features.models import FeatureSegment

    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment_id=segment_id,
        environment=environment,
        environment_feature_version=version,
    )

    if priority is not None:
        feature_segment.to(priority)

    segment_state: FeatureState = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        environment_feature_version=version,
        enabled=enabled,
    )

    return segment_state


def _update_segment_priority(feature_state: FeatureState, priority: int) -> None:
    feature_segment = feature_state.feature_segment
    if feature_segment:
        feature_segment.to(priority)


def update_flag_option_b(
    environment: Environment, feature: Feature, change_set: FlagChangeSetOptionB
) -> None:
    with transaction.atomic():
        if environment.use_v2_feature_versioning:
            _update_flag_option_b_for_versioning_v2(environment, feature, change_set)
        else:
            _update_flag_option_b_for_versioning_v1(environment, feature, change_set)


def _apply_environment_default_change_set(
    env_default_state: FeatureState,
    feature: Feature,
    environment_default: EnvironmentDefaultChangeSet,
) -> None:
    if environment_default.enabled is not None:
        env_default_state.enabled = environment_default.enabled
        env_default_state.save()

    if environment_default.value is not None:
        _update_feature_state_value(
            env_default_state.feature_state_value, environment_default.value
        )

    update_environment_multivariate_options(
        env_default_state, feature, environment_default.multivariate_values
    )


def _update_flag_option_b_for_versioning_v2(
    environment: Environment, feature: Feature, change_set: FlagChangeSetOptionB
) -> None:
    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment,
        feature=feature,
        created_by=change_set.author.user,
        created_by_api_key=change_set.author.api_key,
    )

    def get_environment_default() -> FeatureState:
        environment_default: FeatureState = new_version.feature_states.get(
            feature_segment__isnull=True, identity_id=None
        )
        return environment_default

    if change_set.environment_default is not None:
        _apply_environment_default_change_set(
            get_environment_default(), feature, change_set.environment_default
        )

    for override in change_set.segment_overrides:
        try:
            segment_state = new_version.feature_states.get(
                feature_segment__segment_id=override.segment_id
            )
            if override.enabled is not None:
                segment_state.enabled = override.enabled
                segment_state.save()

            if override.value is not None:
                _update_feature_state_value(
                    segment_state.feature_state_value, override.value
                )
            update_multivariate_values(segment_state, override.multivariate_values)

            if override.priority is not None:
                _update_segment_priority(segment_state, override.priority)
        except FeatureState.DoesNotExist:
            enabled, inherited_value = _resolve_new_override_inheritance(
                override.enabled,
                override.value,
                get_environment_default,
            )
            segment_state = _create_segment_override(
                feature=feature,
                environment=environment,
                segment_id=override.segment_id,
                enabled=enabled,
                priority=override.priority,
                version=new_version,
            )

            if override.value is not None:
                _update_feature_state_value(
                    segment_state.feature_state_value, override.value
                )
            elif inherited_value is not None:
                segment_state.feature_state_value.copy_from(inherited_value)
            update_multivariate_values(segment_state, override.multivariate_values)

    new_version.publish(
        published_by=change_set.author.user,
        published_by_api_key=change_set.author.api_key,
    )


def _update_flag_option_b_for_versioning_v1(
    environment: Environment, feature: Feature, change_set: FlagChangeSetOptionB
) -> None:
    if change_set.environment_default is not None:
        _apply_environment_default_change_set(
            _get_environment_default_feature_state(environment, feature),
            feature,
            change_set.environment_default,
        )

    for override in change_set.segment_overrides:
        # TODO: optimise this once this is out of the
        # experimentation stage
        segment_states = get_environment_flags_dict(
            environment=environment,
            feature_name=feature.name,
            additional_filters=Q(feature_segment__segment_id=override.segment_id),
        )

        if len(segment_states) == 0:
            enabled, inherited_value = _resolve_new_override_inheritance(
                override.enabled,
                override.value,
                lambda: _get_environment_default_feature_state(environment, feature),
            )
            segment_state = _create_segment_override(
                feature=feature,
                environment=environment,
                segment_id=override.segment_id,
                enabled=enabled,
                priority=override.priority,
                version=None,  # V1 versioning doesn't use versions
            )

            if override.value is not None:
                _update_feature_state_value(
                    segment_state.feature_state_value, override.value
                )
            elif inherited_value is not None:
                segment_state.feature_state_value.copy_from(inherited_value)
            update_multivariate_values(segment_state, override.multivariate_values)
        else:
            assert len(segment_states) == 1
            segment_state = list(segment_states.values())[0]
            if override.enabled is not None:
                segment_state.enabled = override.enabled
                segment_state.save()

            if override.value is not None:
                _update_feature_state_value(
                    segment_state.feature_state_value, override.value
                )
            update_multivariate_values(segment_state, override.multivariate_values)

            if override.priority is not None:
                _update_segment_priority(segment_state, override.priority)


def delete_segment_override(
    environment: "Environment",
    feature: "Feature",
    segment_id: int,
    author: AuthorData,
) -> None:
    if environment.use_v2_feature_versioning:
        _delete_segment_override_v2(environment, feature, segment_id, author)
    else:
        _delete_segment_override_v1(environment, feature, segment_id)


def _delete_segment_override_v1(
    environment: "Environment",
    feature: "Feature",
    segment_id: int,
) -> None:
    deleted_count, _ = FeatureSegment.objects.filter(
        feature=feature,
        segment_id=segment_id,
        environment=environment,
    ).delete()
    if deleted_count == 0:
        raise NotFound(f"Segment override for segment {segment_id} does not exist")


def _delete_segment_override_v2(
    environment: "Environment",
    feature: "Feature",
    segment_id: int,
    author: AuthorData,
) -> None:
    current_version = get_current_live_environment_feature_version(
        environment.id, feature.id
    )
    if (
        not current_version
        or not current_version.feature_states.filter(
            feature_segment__segment_id=segment_id
        ).exists()
    ):
        raise NotFound(f"Segment override for segment {segment_id} does not exist")

    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment,
        feature=feature,
        created_by=author.user,
        created_by_api_key=author.api_key,
    )

    segment_feature_state = new_version.feature_states.get(
        feature_segment__segment_id=segment_id
    )
    segment_feature_state.feature_segment.delete()

    new_version.publish(published_by=author.user, published_by_api_key=author.api_key)


def get_updated_feature_states_for_version(
    version: EnvironmentFeatureVersion,
) -> list[FeatureState]:
    """
    Returns feature states that changed compared to the previous version.
    """

    def get_match_key(fs: FeatureState) -> tuple[int | None, int | None]:
        segment_id = fs.feature_segment.segment_id if fs.feature_segment else None
        return (fs.identity_id, segment_id)

    def multivariate_values_changed(
        fs: FeatureState, previous_fs: FeatureState
    ) -> bool:
        current_mv_values = {
            mv.multivariate_feature_option_id: mv.percentage_allocation
            for mv in fs.multivariate_feature_state_values.all()
        }
        previous_mv_values = {
            mv.multivariate_feature_option_id: mv.percentage_allocation
            for mv in previous_fs.multivariate_feature_state_values.all()
        }
        return current_mv_values != previous_mv_values

    previous_version = version.get_previous_version()
    previous_feature_states_map = (
        {get_match_key(fs): fs for fs in previous_version.feature_states.all()}
        if previous_version
        else {}
    )

    changed_feature_states = []
    for feature_state in version.feature_states.all():
        previous_fs = previous_feature_states_map.get(get_match_key(feature_state))

        if previous_fs is None or (
            feature_state.enabled != previous_fs.enabled
            or feature_state.get_feature_state_value()
            != previous_fs.get_feature_state_value()
            or multivariate_values_changed(feature_state, previous_fs)
        ):
            changed_feature_states.append(feature_state)

    return changed_feature_states


def _get_feature_states_queryset(
    environment: "Environment",
    feature_name: str | None = None,
    additional_filters: Q = None,  # type: ignore[assignment]
    additional_select_related_args: typing.Iterable[str] = None,  # type: ignore[assignment]
    additional_prefetch_related_args: typing.Iterable[
        typing.Union[str, Prefetch[typing.Any]]
    ] = None,  # type: ignore[assignment]
    from_replica: bool = False,
) -> QuerySet[FeatureState]:
    additional_select_related_args = additional_select_related_args or tuple()
    additional_prefetch_related_args = additional_prefetch_related_args or tuple()

    feature_state_manager = FeatureState.objects
    if from_replica:
        feature_state_manager = using_database_replica(FeatureState.objects)

    queryset = (
        feature_state_manager.get_live_feature_states(
            environment=environment,
            additional_filters=additional_filters,
        )
        .select_related(
            "environment",
            "feature",
            "feature_state_value",
            "environment_feature_version",
            "feature_segment",
            *additional_select_related_args,
        )
        .prefetch_related(*additional_prefetch_related_args)
    )

    if feature_name:
        queryset = queryset.filter(feature__name__iexact=feature_name)

    return queryset


def _get_distinct_key(
    feature_state: FeatureState,
) -> tuple[int, int | None, int | None]:
    return (
        feature_state.feature_id,
        getattr(feature_state.feature_segment, "segment_id", None),
        feature_state.identity_id,
    )
