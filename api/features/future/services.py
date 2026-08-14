"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from collections.abc import Collection, Sequence
from itertools import groupby
from operator import attrgetter
from typing import NamedTuple

import structlog
from django.db import transaction
from django.db.models import Q

from api_keys.user import APIKeyUser
from environments.models import Environment
from features.future.exceptions import DuplicatePriorityError
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
from users.models import FFAdminUser

logger = structlog.get_logger("features")


def _get_feature_states(
    environment: Environment, feature: Feature
) -> list[FeatureState]:
    return get_environment_flags_list(
        environment,
        additional_filters=Q(
            feature_id=feature.id,
            identity__isnull=True,  # Identity overrides are unsupported
        ),
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
            "feature_segment",
            "feature_state_value",
        ).prefetch_related("multivariate_feature_state_values")
    )


def _write_variants(feature_state: FeatureState, variants: Sequence[Variant]) -> None:
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


def _write_segment_override(
    feature_state: FeatureState,
    changes: SegmentOverrideRequest,
    *,
    replace: bool,
    environment_default: FeatureState,
) -> None:
    """Write an override, inheriting from the environment default what it omits."""
    feature_segment = feature_state.feature_segment
    if feature_segment is None:  # pragma: no cover
        raise ValueError("Feature state is not a segment override.")

    if (priority := changes.get("priority")) is not None:
        feature_segment.priority = priority
        feature_segment.save(update_fields=["priority"])

    if replace or "enabled" in changes:
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
    # Deleting a `FeatureSegment` instance decrements every greater priority.
    feature_segments.filter(segment_id__in=segment_ids).delete()


def _check_priorities(
    environment: Environment,
    feature: Feature,
    version: EnvironmentFeatureVersion | None,
) -> None:
    """Precedence between two segment overrides sharing a priority is undefined."""
    feature_segments = (
        FeatureSegment.objects.filter(
            environment=environment,
            feature=feature,
            environment_feature_version=version,
        )
        .select_related("segment")
        .order_by("priority", "segment_id")
    )
    for _priority, sharing in groupby(feature_segments, attrgetter("priority")):
        segments = [feature_segment.segment for feature_segment in sharing]
        if len(segments) > 1:
            raise DuplicatePriorityError(segments)


class WrittenSegmentOverrides(NamedTuple):
    created: list[int]
    updated: list[int]
    deleted: list[int]


def _write_segment_overrides(
    *,
    environment: Environment,
    feature: Feature,
    version: EnvironmentFeatureVersion | None,
    environment_default: FeatureState,
    overrides: dict[int, FeatureState],
    changes: Sequence[SegmentOverrideRequest],
    replace: bool,
) -> WrittenSegmentOverrides:
    written = WrittenSegmentOverrides([], [], [])

    if replace:
        written.deleted.extend(
            sorted(overrides.keys() - {change["segment"]["id"] for change in changes})
        )
        _delete_segment_overrides(
            environment=environment,
            feature=feature,
            version=version,
            segment_ids=written.deleted,
        )

    for position, change in enumerate(changes):
        segment_id = change["segment"]["id"]
        if feature_state := overrides.get(segment_id):
            written.updated.append(segment_id)
        else:
            feature_state = _create_segment_override(
                environment=environment,
                feature=feature,
                version=version,
                segment_id=segment_id,
                priority=change.get("priority", position),
            )
            written.created.append(segment_id)
        _write_segment_override(
            feature_state,
            change,
            replace=replace or segment_id in written.created,
            environment_default=environment_default,
        )

    _check_priorities(environment, feature, version)

    return written


def update_flag(
    *,
    environment: Environment,
    feature: Feature,
    changes: UpdateFlagRequest,
    replace: bool,
    author: FFAdminUser | APIKeyUser,
) -> UpdateFlagResponse:
    """Write the given parts of a flag, whichever versioning the environment uses."""
    writes_nothing = not changes if replace else not any(changes.values())
    if writes_nothing:
        return get_flag(environment=environment, feature=feature)

    written = WrittenSegmentOverrides([], [], [])

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
            written = _write_segment_overrides(
                environment=environment,
                feature=feature,
                version=version,
                environment_default=environment_default,
                overrides={
                    feature_segment.segment_id: feature_state
                    for feature_state in feature_states
                    if (feature_segment := feature_state.feature_segment) is not None
                },
                changes=override_changes,
                replace=replace,
            )

        if version is not None:
            # `UserABC.__subclasshook__` matches any user against `APIKeyUser`
            published_by = author if isinstance(author, FFAdminUser) else None
            version.publish(
                published_by=published_by,
                published_by_api_key=None if published_by else author.key,
            )

    logger.info(
        "flag.updated",
        organisation__id=environment.project.organisation_id,
        project__id=environment.project_id,
        environment__id=environment.id,
        feature__id=feature.id,
        segment_overrides__created__segment__ids=written.created,
        segment_overrides__updated__segment__ids=written.updated,
        segment_overrides__deleted__segment__ids=written.deleted,
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
