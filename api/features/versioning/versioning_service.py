import typing

from common.core.utils import using_database_replica
from django.db.models import Prefetch, Q, QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from environments.models import Environment
from features.feature_states.models import FeatureValueType
from features.models import Feature, FeatureSegment, FeatureState, FeatureStateValue
from features.multivariate.models import MultivariateFeatureStateValue
from features.versioning.dataclasses import (
    FlagChangeSet,
    MultivariateValueChangeSet,
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
        # Every feature state in the queryset belongs to `environment`;
        # populating the relation up front keeps `feature_state.environment`
        # accesses from querying the database.
        feature_state.environment = environment
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


def update_flag(
    environment: Environment, feature: Feature, change_set: FlagChangeSet
) -> FeatureState:
    if environment.use_v2_feature_versioning:
        return _update_flag_for_versioning_v2(environment, feature, change_set)
    else:
        return _update_flag_for_versioning_v1(environment, feature, change_set)


def _update_flag_for_versioning_v2(
    environment: Environment, feature: Feature, change_set: FlagChangeSet
) -> FeatureState:
    from features.models import FeatureState

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

            target_feature_state = FeatureState.objects.create(
                feature=feature,
                environment=environment,
                feature_segment=feature_segment,
                environment_feature_version=new_version,
                enabled=change_set.enabled,
            )
    else:
        # Environment default - always exists
        target_feature_state = new_version.feature_states.get(
            feature_segment__isnull=True,
            identity_id=None,
        )

    target_feature_state.enabled = change_set.enabled
    target_feature_state.save()

    _update_feature_state_value(
        target_feature_state.feature_state_value,
        change_set.feature_state_value,
        change_set.type_,
    )
    update_multivariate_values(target_feature_state, change_set.multivariate_values)

    if change_set.segment_id is not None and change_set.segment_priority is not None:
        _update_segment_priority(target_feature_state, change_set.segment_priority)

    new_version.publish(
        published_by=change_set.author.user,
        published_by_api_key=change_set.author.api_key,
    )

    return target_feature_state


def _update_flag_for_versioning_v1(
    environment: Environment, feature: Feature, change_set: FlagChangeSet
) -> FeatureState:
    from features.models import FeatureState

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

        target_feature_state: FeatureState = FeatureState.objects.create(
            feature=feature,
            environment=environment,
            feature_segment=feature_segment,
            enabled=change_set.enabled,
        )
    else:
        assert len(latest_feature_states) == 1
        target_feature_state = list(latest_feature_states.values())[0]
        target_feature_state.enabled = change_set.enabled
        target_feature_state.save()

    _update_feature_state_value(
        target_feature_state.feature_state_value,
        change_set.feature_state_value,
        change_set.type_,
    )
    update_multivariate_values(target_feature_state, change_set.multivariate_values)

    if change_set.segment_id is not None and change_set.segment_priority is not None:
        _update_segment_priority(target_feature_state, change_set.segment_priority)

    return target_feature_state


def _update_feature_state_value(
    fsv: FeatureStateValue, value: str, type_: FeatureValueType
) -> None:
    fsv.set_value(value, type_)
    fsv.save()


def update_multivariate_values(
    feature_state: FeatureState,
    values: list[MultivariateValueChangeSet] | None,
) -> None:
    if values is None:
        return

    existing = {
        mv.multivariate_feature_option_id: mv
        for mv in feature_state.multivariate_feature_state_values.all()
    }

    passed_option_ids = {value.multivariate_feature_option_id for value in values}
    effective_total = sum(value.percentage_allocation for value in values) + sum(
        mv.percentage_allocation
        for option_id, mv in existing.items()
        if option_id not in passed_option_ids
    )
    if effective_total > 100:
        raise ValidationError(
            "Multivariate allocations for the feature state must not exceed "
            f"100%, got {effective_total}%."
        )

    for value in values:
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


def _update_segment_priority(feature_state: FeatureState, priority: int) -> None:
    feature_segment = feature_state.feature_segment
    if feature_segment:
        feature_segment.to(priority)


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

    queryset = feature_state_manager.get_live_feature_states(
        environment=environment,
        additional_filters=additional_filters,
    )

    if feature_name:
        queryset = queryset.filter(feature__name__iexact=feature_name)

    return queryset.select_related(
        "feature",
        "feature_state_value",
        "environment_feature_version",
        "feature_segment",
        *additional_select_related_args,
    ).prefetch_related(*additional_prefetch_related_args)


def _get_distinct_key(
    feature_state: FeatureState,
) -> tuple[int, int | None, int | None]:
    return (
        feature_state.feature_id,
        getattr(feature_state.feature_segment, "segment_id", None),
        feature_state.identity_id,
    )
