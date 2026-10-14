"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from collections.abc import Collection, Iterable, Sequence
from itertools import count, islice
from typing import NamedTuple

import structlog
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from audit.tasks import create_segment_priorities_changed_audit_log
from core.dataclasses import AuthorData
from environments.models import Environment
from features.dependencies.models import SegmentFlagReference
from features.dependencies.services import (
    report_flag_dependencies,
    validate_segment_flag_dependencies,
)
from features.dependencies.types import FeatureName
from features.feature_segments.limits import (
    SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE,
    exceeds_segment_override_limit,
)
from features.feature_types import MULTIVARIATE
from features.future.exceptions import (
    DuplicatePriorityError,
    SegmentOverrideNotFoundError,
)
from features.future.mappers import (
    map_environment_default,
    map_segment_override,
    map_variants,
)
from features.future.types import (
    EnvironmentDefaultRequest,
    SegmentOverrideRequest,
    UpdateFlagRequest,
    UpdateFlagResponse,
    Variant,
)
from features.models import Feature, FeatureSegment, FeatureState, FeatureStateValue
from features.multivariate.models import MultivariateFeatureStateValue
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.versioning_service import get_environment_flags_list
from segments.models import Segment
from segments.services import check_segment_is_not_system
from util.db import with_delete_hooks

logger = structlog.get_logger("features")


class _OverriddenSegments(NamedTuple):
    created: list[int]
    updated: list[int]
    deleted: list[int]


def _get_feature_states(
    environment: Environment, feature: Feature
) -> list[FeatureState]:
    return get_environment_flags_list(
        environment,
        additional_filters=Q(
            feature_id=feature.id,
            identity__isnull=True,  # Identity overrides are unsupported
        ),
        additional_select_related_args=["feature_segment__segment"],
        additional_prefetch_related_args=["multivariate_feature_state_values"],
    )


def _create_draft_version(
    environment: Environment, feature: Feature
) -> EnvironmentFeatureVersion | None:
    """Create an unpublished version of the flag, cloned from its live state."""
    if not environment.use_v2_feature_versioning:
        return None
    return EnvironmentFeatureVersion.objects.create(  # type: ignore[no-any-return]
        environment=environment, feature=feature
    )


def _get_feature_states_to_write(
    environment: Environment,
    feature: Feature,
    version: EnvironmentFeatureVersion | None,
) -> list[FeatureState]:
    if version is None:
        return _get_feature_states(environment, feature)
    return list(
        version.feature_states.select_related(
            "feature_segment__segment",
            "feature_state_value",
        ).prefetch_related("multivariate_feature_state_values")
    )


def _get_overrides_by_segment_id(
    feature_states: Sequence[FeatureState],
) -> dict[int, FeatureState]:
    return {
        feature_segment.segment_id: feature_state
        for feature_state in feature_states
        if (feature_segment := feature_state.feature_segment) is not None
    }


def _get_feature_segment_priorities(
    overrides: dict[int, FeatureState],
) -> dict[int, int]:
    return {
        feature_state.feature_segment.id: feature_state.feature_segment.priority
        for feature_state in overrides.values()
        if feature_state.feature_segment is not None
    }


def check_variants(feature: Feature, variant_sets: Iterable[Sequence[Variant]]) -> None:
    """Refuse weighting anything but each of a feature's variants, exactly once,
    up to 100 in total."""
    feature_variant_ids: set[int] | None = None
    for variants in variant_sets:
        if feature.type != MULTIVARIATE:
            raise ValidationError("Feature is not multivariate.")
        given_ids = [variant["id"] for variant in variants]
        if duplicate_ids := sorted(
            {id_ for id_ in given_ids if given_ids.count(id_) > 1}
        ):
            raise ValidationError(f"Duplicate variant: {duplicate_ids[0]}.")
        if feature_variant_ids is None:
            feature_variant_ids = set(
                feature.multivariate_options.values_list("id", flat=True)
            )
        if unknown_ids := sorted(set(given_ids) - feature_variant_ids):
            raise ValidationError(f"Variant not found: {unknown_ids[0]}.")
        if feature_variant_ids - set(given_ids):
            raise ValidationError("Must include all feature's variants.")
        if (total_weight := sum(variant["weight"] for variant in variants)) > 100:
            raise ValidationError(
                f"Total weight must not exceed 100, got {total_weight}."
            )


def _write_variants(feature_state: FeatureState, variants: Sequence[Variant]) -> None:
    """Weight a feature state's variants, checked first with `check_variants`."""
    weighted = {
        multivariate_value.multivariate_feature_option_id: multivariate_value
        for multivariate_value in feature_state.multivariate_feature_state_values.all()
    }
    for variant in variants:
        if multivariate_value := weighted.get(variant["id"]):
            multivariate_value.percentage_allocation = variant["weight"]
            multivariate_value.save(update_fields=["percentage_allocation"])
        else:
            MultivariateFeatureStateValue.objects.create(
                feature_state=feature_state,
                multivariate_feature_option_id=variant["id"],
                percentage_allocation=variant["weight"],
            )


def _clear_value(feature_state_value: FeatureStateValue) -> None:
    value_fields = ["string_value", "integer_value", "boolean_value"]
    for value_field in value_fields:
        setattr(feature_state_value, value_field, None)
    feature_state_value.save(update_fields=value_fields)


def _write_environment_default(
    feature_state: FeatureState,
    changes: EnvironmentDefaultRequest,
    *,
    replace: bool,
) -> None:
    if replace or "enabled" in changes:
        feature_state.enabled = changes.get("enabled", False)
        feature_state.save(update_fields=["enabled"])

    feature_state_value = feature_state.feature_state_value
    if (value := changes.get("value")) is not None:
        feature_state_value.set_value(value["value"], value["type"])
        feature_state_value.save()
    elif replace:
        _clear_value(feature_state_value)

    if (variants := changes.get("variants")) is not None:
        _write_variants(feature_state, variants)


def _check_shifted_system_segments(
    feature_segment: FeatureSegment, priority: int, *, enabled: bool
) -> None:
    if enabled:
        for shifted in (
            feature_segment.get_ordering_queryset()
            .filter(
                priority__gte=min(feature_segment.priority, priority),
                priority__lte=max(feature_segment.priority, priority),
            )
            .select_related("segment")
        ):
            check_segment_is_not_system(shifted.segment)


def _write_segment_override(
    feature_state: FeatureState,
    changes: SegmentOverrideRequest,
    *,
    replace: bool,
    environment_default: FeatureState,
    created: bool,
    shift_priority: bool,
    protect_shifted_system_segments: bool,
) -> None:
    """Write an override, inheriting from the environment default what it omits."""
    feature_segment = feature_state.feature_segment
    if feature_segment is None:  # pragma: no cover
        raise ValueError("Feature state is not a segment override.")

    if (priority := changes.get("priority")) is not None:
        if shift_priority:
            _check_shifted_system_segments(
                feature_segment,
                priority,
                enabled=protect_shifted_system_segments,
            )
            feature_segment.to(priority)
        else:
            feature_segment.priority = priority
            feature_segment.save(update_fields=["priority"])

    # New overrides get their enabled value on creation, so the audit log
    # records a creation rather than a change from the environment default.
    if not created and (replace or "enabled" in changes):
        feature_state.enabled = changes.get("enabled", environment_default.enabled)
        feature_state.save(update_fields=["enabled"])

    feature_state_value = feature_state.feature_state_value
    if (value := changes.get("value")) is not None:
        feature_state_value.set_value(value["value"], value["type"])
        feature_state_value.save()
    elif replace:
        feature_state_value.copy_from(environment_default.feature_state_value)

    if (variants := changes.get("variants")) is not None:
        _write_variants(feature_state, variants)
    elif replace:
        _write_variants(feature_state, map_variants(environment_default))


def _create_segment_override(
    *,
    environment: Environment,
    feature: Feature,
    version: EnvironmentFeatureVersion | None,
    segment_id: int,
    priority: int,
    enabled: bool,
) -> FeatureState:
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        environment=environment,
        environment_feature_version=version,
        segment_id=segment_id,
        priority=priority,
    )
    return FeatureState.objects.create(  # type: ignore[no-any-return]
        feature=feature,
        environment=environment,
        environment_feature_version=version,
        feature_segment=feature_segment,
        enabled=enabled,
    )


def _delete_segment_overrides(
    *,
    environment: Environment,
    feature: Feature,
    version: EnvironmentFeatureVersion | None,
    segment_ids: Collection[int],
) -> None:
    feature_segments = (
        FeatureSegment.objects.filter(environment=environment, feature=feature)
        if version is None
        else version.feature_segments.all()
    )
    # Deleting the queryset, rather than each instance, leaves the other
    # priorities as they are.
    with with_delete_hooks(
        feature_segments.filter(segment_id__in=segment_ids)
    ) as deleted_feature_segments:
        deleted_feature_segments.delete()


def _check_priorities(
    environment: Environment,
    feature: Feature,
    version: EnvironmentFeatureVersion | None,
) -> None:
    """Precedence between two segment overrides sharing a priority is undefined."""
    duplicate = (
        FeatureSegment.objects.filter(
            environment=environment,
            feature=feature,
            environment_feature_version=version,
        )
        .values("priority")
        .annotate(count=Count("priority"))
        .filter(count__gt=1)
        .order_by("priority")
        .values_list("priority", flat=True)
        .first()
    )
    if duplicate is not None:
        raise DuplicatePriorityError(f"Duplicate priority: {duplicate}.")


def _write_segment_overrides(
    *,
    environment: Environment,
    feature: Feature,
    version: EnvironmentFeatureVersion | None,
    environment_default: FeatureState,
    overrides: dict[int, FeatureState],
    changes: Sequence[SegmentOverrideRequest],
    replace: bool,
    overwrite_system_segment_overrides: bool,
    shift_priorities: bool,
) -> _OverriddenSegments:
    segments = _OverriddenSegments([], [], [])
    changed_segment_ids = {change["segment"]["id"] for change in changes}

    overridden_segments = {
        feature_segment.segment_id: feature_segment.segment
        for feature_state in overrides.values()
        if (feature_segment := feature_state.feature_segment)
    }
    if not overwrite_system_segment_overrides:
        for segment in [
            *(
                overridden_segments[id_]
                for id_ in changed_segment_ids & overrides.keys()
            ),
            *Segment.objects.filter(id__in=changed_segment_ids - overrides.keys()),
        ]:
            check_segment_is_not_system(segment)

    if replace:
        segments.deleted.extend(
            sorted(
                segment_id
                for segment_id, segment in overridden_segments.items()
                if segment_id not in changed_segment_ids
                and (
                    overwrite_system_segment_overrides or not segment.is_system_segment
                )
            )
        )

    if not overwrite_system_segment_overrides:
        if exceeds_segment_override_limit(
            environment,
            segment_ids_to_create_overrides=[
                change["segment"]["id"]
                for change in changes
                if change["segment"]["id"] not in overrides
            ],
            segment_ids_to_delete_overrides=segments.deleted,
            exclusive=True,
        ):
            raise ValidationError(
                {"segment_overrides": [SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE]}
            )

    if replace:
        _delete_segment_overrides(
            environment=environment,
            feature=feature,
            version=version,
            segment_ids=segments.deleted,
        )

    # Overrides kept by replacing, i.e. system segment ones, hold their priorities.
    held_priorities = {
        feature_state.feature_segment.priority
        for segment_id, feature_state in overrides.items()
        if replace
        and feature_state.feature_segment
        and segment_id not in changed_segment_ids
        and segment_id not in segments.deleted
    }
    default_priorities = list(
        islice(
            (priority for priority in count() if priority not in held_priorities),
            len(changes),
        )
    )

    for position, change in enumerate(changes):
        segment_id = change["segment"]["id"]
        if feature_state := overrides.get(segment_id):
            segments.updated.append(segment_id)
        else:
            feature_state = _create_segment_override(
                environment=environment,
                feature=feature,
                version=version,
                segment_id=segment_id,
                priority=change.get("priority", default_priorities[position]),
                enabled=change.get("enabled", environment_default.enabled),
            )
            segments.created.append(segment_id)
        _write_segment_override(
            feature_state,
            change,
            replace=replace or segment_id in segments.created,
            environment_default=environment_default,
            created=segment_id in segments.created,
            shift_priority=shift_priorities,
            protect_shifted_system_segments=(
                shift_priorities and not overwrite_system_segment_overrides
            ),
        )

    _check_priorities(environment, feature, version)

    return segments


def _get_prerequisite_feature_names(
    segments: _OverriddenSegments,
) -> tuple[set[FeatureName], set[FeatureName]]:
    """Return the prerequisite feature names the flag gains and loses."""
    created: set[FeatureName] = set()
    deleted: set[FeatureName] = set()
    for segment_id, feature_name in SegmentFlagReference.objects.filter(
        segment_id__in=[*segments.created, *segments.deleted]
    ).values_list("segment_id", "prerequisite_feature__name"):
        names = created if segment_id in segments.created else deleted
        names.add(feature_name)
    return created, deleted


def update_flag(
    *,
    environment: Environment,
    feature: Feature,
    changes: UpdateFlagRequest,
    replace: bool,
    author: AuthorData,
    overwrite_system_segment_overrides: bool,
    shift_segment_override_priorities: bool = False,
) -> UpdateFlagResponse:
    """Write the given parts of a flag, whichever versioning the environment uses.

    Overrides of system segments can only be changed by passing
    `overwrite_system_segment_overrides=True`. By default, segment override
    priorities are absolute; `shift_segment_override_priorities=True` moves
    other overrides out of the way instead.
    """
    writes_nothing = not changes if replace else not any(changes.values())
    if writes_nothing:
        return get_flag(environment=environment, feature=feature)
    check_variants(
        feature,
        [
            variants
            for flag_state in [
                changes.get("environment_default", {}),
                *changes.get("segment_overrides", []),
            ]
            if (variants := flag_state.get("variants")) is not None
        ],
    )

    segments = _OverriddenSegments([], [], [])
    previous_priorities: dict[int, int] = {}
    priorities_changed = False

    with transaction.atomic():
        version = _create_draft_version(environment, feature)
        feature_states = _get_feature_states_to_write(environment, feature, version)
        environment_default = next(
            feature_state
            for feature_state in feature_states
            if feature_state.feature_segment_id is None
        )

        if (default_changes := changes.get("environment_default")) is not None:
            _write_environment_default(
                environment_default, default_changes, replace=replace
            )

        if (override_changes := changes.get("segment_overrides")) is not None:
            overrides = _get_overrides_by_segment_id(feature_states)
            previous_priorities = _get_feature_segment_priorities(overrides)
            segments = _write_segment_overrides(
                environment=environment,
                feature=feature,
                version=version,
                environment_default=environment_default,
                overrides=overrides,
                changes=override_changes,
                replace=replace,
                overwrite_system_segment_overrides=overwrite_system_segment_overrides,
                shift_priorities=shift_segment_override_priorities,
            )
            # Versioned environments audit reorders through their version history.
            priorities_changed = version is None and previous_priorities != (
                _get_feature_segment_priorities(overrides)
            )

        if version is not None:
            version.publish(
                published_by=author.user, published_by_api_key=author.api_key
            )

        for segment in Segment.objects.filter(id__in=segments.created):
            validate_segment_flag_dependencies(segment)
        created, deleted = _get_prerequisite_feature_names(segments)
        report_flag_dependencies(
            environment=environment,
            feature=feature,
            created=created,
            deleted=deleted,
        )

    if priorities_changed:
        create_segment_priorities_changed_audit_log.delay(
            kwargs={
                "previous_id_priority_pairs": list(previous_priorities.items()),
                "feature_segment_ids": list(previous_priorities),
                "user_id": author.user.id if author.user else None,
                "master_api_key_id": author.api_key.id if author.api_key else None,
                "changed_at": timezone.now().isoformat(),
            }
        )

    logger.info(
        "flag.updated",
        organisation__id=environment.project.organisation_id,
        project__id=environment.project_id,
        environment__id=environment.id,
        feature__id=feature.id,
        segment_overrides__created__segment__ids=segments.created,
        segment_overrides__updated__segment__ids=segments.updated,
        segment_overrides__deleted__segment__ids=segments.deleted,
    )

    return get_flag(environment=environment, feature=feature)


def delete_segment_override(
    *,
    environment: Environment,
    feature: Feature,
    segment_id: int,
    author: AuthorData,
    overwrite_system_segment_overrides: bool,
) -> UpdateFlagResponse:
    """Remove a flag's override for one segment, leaving the rest of the flag alone.

    Overrides of system segments can only be removed by passing
    `overwrite_system_segment_overrides=True`.
    """
    with transaction.atomic():
        version = _create_draft_version(environment, feature)
        feature_states = _get_feature_states_to_write(environment, feature, version)

        if not (
            override := _get_overrides_by_segment_id(feature_states).get(segment_id)
        ):
            raise SegmentOverrideNotFoundError()
        if not overwrite_system_segment_overrides and override.feature_segment:
            check_segment_is_not_system(override.feature_segment.segment)

        _delete_segment_overrides(
            environment=environment,
            feature=feature,
            version=version,
            segment_ids=[segment_id],
        )

        if version is not None:
            version.publish(
                published_by=author.user, published_by_api_key=author.api_key
            )

        _, deleted = _get_prerequisite_feature_names(
            _OverriddenSegments([], [], [segment_id])
        )
        report_flag_dependencies(
            environment=environment,
            feature=feature,
            created=[],
            deleted=deleted,
        )

    logger.info(
        "flag.updated",
        organisation__id=environment.project.organisation_id,
        project__id=environment.project_id,
        environment__id=environment.id,
        feature__id=feature.id,
        segment_overrides__created__segment__ids=[],
        segment_overrides__updated__segment__ids=[],
        segment_overrides__deleted__segment__ids=[segment_id],
    )

    return get_flag(environment=environment, feature=feature)


def get_flag(*, environment: Environment, feature: Feature) -> UpdateFlagResponse:
    """Read what a flag serves in an environment."""
    feature_states = _get_feature_states(environment, feature)
    return UpdateFlagResponse(
        environment_default=map_environment_default(
            next(
                feature_state
                for feature_state in feature_states
                if feature_state.feature_segment_id is None
            )
        ),
        segment_overrides=sorted(
            filter(None, map(map_segment_override, feature_states)),
            key=lambda override: (override["priority"], override["segment"]["id"]),
        ),
    )
