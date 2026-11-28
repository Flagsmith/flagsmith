"""https://docs.flagsmith.com/managing-flags/updating-flags"""

import json
from collections.abc import Callable, Collection, Iterable, Sequence
from itertools import count, islice
from typing import Any, NamedTuple

import structlog
from common.features.serializers import FeatureStateValueSerializer
from django.db import transaction
from django.db.models import Count, Q
from rest_framework.exceptions import ValidationError

from core.dataclasses import AuthorData
from environments.models import Environment
from features.dependencies.services import (
    report_flag_dependency_changes,
    validate_segment_flag_dependencies,
)
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
    FlagValue,
    SegmentOverrideRequest,
    UpdateFlagRequest,
    UpdateFlagResponse,
    Variant,
)
from features.models import Feature, FeatureSegment, FeatureState, FeatureStateValue
from features.multivariate.models import MultivariateFeatureStateValue
from features.versioning.models import EnvironmentFeatureVersion, VersionChangeSet
from features.versioning.versioning_service import get_environment_flags_list
from features.workflows.core.models import ChangeRequest
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


def _write_value(
    feature_state_value: FeatureStateValue, value: FlagValue | None
) -> None:
    if value is None:
        _clear_value(feature_state_value)
        return
    feature_state_value.set_value(value["value"], value["type"])
    feature_state_value.save()


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
    if "value" in changes:
        _write_value(feature_state_value, changes["value"])
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
    created: bool,
) -> None:
    """Write an override, inheriting from the environment default what it omits."""
    feature_segment = feature_state.feature_segment
    if feature_segment is None:  # pragma: no cover
        raise ValueError("Feature state is not a segment override.")

    if (priority := changes.get("priority")) is not None:
        feature_segment.priority = priority
        feature_segment.save(update_fields=["priority"])

    # New overrides get their enabled value on creation, so the audit log
    # records a creation rather than a change from the environment default.
    if not created and (replace or "enabled" in changes):
        feature_state.enabled = changes.get("enabled", environment_default.enabled)
        feature_state.save(update_fields=["enabled"])

    feature_state_value = feature_state.feature_state_value
    if "value" in changes:
        _write_value(feature_state_value, changes["value"])
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
        )

    _check_priorities(environment, feature, version)

    return segments


# Feature states in the shape change sets store them: the shape the versioning
# serializers accept, so publishing a change set applies them unchanged.
FeatureStatePayload = dict[str, Any]


class _FlagState(NamedTuple):
    """A flag's feature states, as payloads, keyed by segment for overrides."""

    environment_default: FeatureStatePayload
    overrides: dict[int, FeatureStatePayload]


def _serialize_feature_state(feature_state: FeatureState) -> FeatureStatePayload:
    feature_segment = feature_state.feature_segment
    return {
        "feature_segment": None
        if feature_segment is None
        else {
            "segment": feature_segment.segment_id,
            "priority": feature_segment.priority,
        },
        "enabled": feature_state.enabled,
        "feature_state_value": dict(
            FeatureStateValueSerializer(feature_state.feature_state_value).data
        ),
        "multivariate_feature_state_values": _stage_variants(
            map_variants(feature_state)
        ),
    }


def _get_live_flag_state(environment: Environment, feature: Feature) -> _FlagState:
    feature_states = _get_feature_states(environment, feature)
    return _FlagState(
        environment_default=_serialize_feature_state(
            next(fs for fs in feature_states if fs.feature_segment_id is None)
        ),
        overrides={
            segment_id: _serialize_feature_state(feature_state)
            for segment_id, feature_state in _get_overrides_by_segment_id(
                feature_states
            ).items()
        },
    )


def _get_staged_flag_state(
    change_set: VersionChangeSet, live: _FlagState
) -> _FlagState:
    """The flag as it will be once the change set is published."""
    environment_default = live.environment_default
    overrides = dict(live.overrides)
    for feature_state in change_set.get_parsed_feature_states_to_update():
        if feature_state["feature_segment"] is None:
            environment_default = feature_state
        else:
            overrides[feature_state["feature_segment"]["segment"]] = feature_state
    for feature_state in change_set.get_parsed_feature_states_to_create():
        overrides[feature_state["feature_segment"]["segment"]] = feature_state
    for segment_id in change_set.get_parsed_segment_ids_to_delete_overrides():
        overrides.pop(segment_id, None)
    return _FlagState(environment_default, overrides)


def _stage_value(current: dict[str, Any], value: FlagValue | None) -> dict[str, Any]:
    """Mirror `_write_value`, clearing the value's fields but keeping its type."""
    if value is None:
        return {
            **current,
            "string_value": None,
            "integer_value": None,
            "boolean_value": None,
        }
    feature_state_value = FeatureStateValue()
    feature_state_value.set_value(value["value"], value["type"])
    return dict(FeatureStateValueSerializer(feature_state_value).data)


def _stage_variants(variants: Sequence[Variant]) -> list[dict[str, Any]]:
    return [
        {
            "multivariate_feature_option": variant["id"],
            "percentage_allocation": variant["weight"],
        }
        for variant in variants
    ]


def _stage_environment_default(
    current: FeatureStatePayload,
    changes: EnvironmentDefaultRequest,
    *,
    replace: bool,
) -> FeatureStatePayload:
    """Mirror `_write_environment_default` on a staged payload."""
    staged = {**current}
    if replace or "enabled" in changes:
        staged["enabled"] = changes.get("enabled", False)
    if "value" in changes or replace:
        staged["feature_state_value"] = _stage_value(
            current["feature_state_value"], changes.get("value")
        )
    if (variants := changes.get("variants")) is not None:
        staged["multivariate_feature_state_values"] = _stage_variants(variants)
    return staged


def _stage_segment_override(
    current: FeatureStatePayload | None,
    change: SegmentOverrideRequest,
    *,
    replace: bool,
    environment_default: FeatureStatePayload,
    default_priority: int,
) -> FeatureStatePayload:
    """Mirror `_write_segment_override` on a staged payload.

    A new override starts from the environment default, as it does when written
    live, and what an existing override omits is inherited from it when replacing.
    """
    is_new = current is None
    staged = {**(environment_default if current is None else current)}
    staged["feature_segment"] = {
        "segment": change["segment"]["id"],
        "priority": change.get("priority", default_priority),
    }
    if is_new or replace or "enabled" in change:
        staged["enabled"] = change.get("enabled", environment_default["enabled"])
    if "value" in change:
        staged["feature_state_value"] = _stage_value(
            staged["feature_state_value"], change["value"]
        )
    elif is_new or replace:
        staged["feature_state_value"] = environment_default["feature_state_value"]
    if (variants := change.get("variants")) is not None:
        staged["multivariate_feature_state_values"] = _stage_variants(variants)
    elif is_new or replace:
        staged["multivariate_feature_state_values"] = environment_default[
            "multivariate_feature_state_values"
        ]
    return staged


def _lowest_free_priority(overrides: Iterable[FeatureStatePayload]) -> int:
    used = {override["feature_segment"]["priority"] for override in overrides}
    return next(priority for priority in count() if priority not in used)


def _check_staged_priorities(overrides: Iterable[FeatureStatePayload]) -> None:
    priorities = [override["feature_segment"]["priority"] for override in overrides]
    if duplicates := sorted({p for p in priorities if priorities.count(p) > 1}):
        raise DuplicatePriorityError(f"Duplicate priority: {duplicates[0]}.")


def _apply_flag_update(
    staged: _FlagState,
    changes: UpdateFlagRequest,
    *,
    replace: bool,
    overwrite_system_segment_overrides: bool,
) -> _FlagState:
    """Mirror `_write_environment_default` and `_write_segment_overrides`.

    The environment default is written first, so overrides inherit from its new state.
    """
    environment_default = staged.environment_default
    if (default_changes := changes.get("environment_default")) is not None:
        environment_default = _stage_environment_default(
            environment_default, default_changes, replace=replace
        )

    overrides = dict(staged.overrides)
    if (override_changes := changes.get("segment_overrides")) is not None:
        changed_segment_ids = {change["segment"]["id"] for change in override_changes}
        if not overwrite_system_segment_overrides:
            for segment in Segment.objects.filter(id__in=changed_segment_ids):
                check_segment_is_not_system(segment)
        if replace:
            system_segment_ids = set(
                Segment.objects.filter(
                    id__in=list(overrides), is_system_segment=True
                ).values_list("id", flat=True)
            )
            overrides = {
                segment_id: feature_state
                for segment_id, feature_state in overrides.items()
                if segment_id in changed_segment_ids
                or (
                    not overwrite_system_segment_overrides
                    and segment_id in system_segment_ids
                )
            }
        for change in override_changes:
            segment_id = change["segment"]["id"]
            current = overrides.get(segment_id)
            overrides[segment_id] = _stage_segment_override(
                current,
                change,
                replace=replace,
                environment_default=environment_default,
                default_priority=(
                    current["feature_segment"]["priority"]
                    if current is not None
                    else _lowest_free_priority(overrides.values())
                ),
            )

    return _FlagState(environment_default, overrides)


def _apply_segment_override_deletion(
    staged: _FlagState,
    segment_id: int,
    *,
    overwrite_system_segment_overrides: bool,
) -> _FlagState:
    if segment_id not in staged.overrides:
        raise SegmentOverrideNotFoundError()
    if not overwrite_system_segment_overrides:
        check_segment_is_not_system(Segment.objects.get(id=segment_id))
    return _FlagState(
        staged.environment_default,
        {
            staged_segment_id: feature_state
            for staged_segment_id, feature_state in staged.overrides.items()
            if staged_segment_id != segment_id
        },
    )


def _validate_change_request(
    environment: Environment, change_request: ChangeRequest
) -> None:
    if change_request.environment_id != environment.id:
        raise ValidationError(
            {"change_request": "Change request belongs to a different environment."}
        )
    if change_request.committed_at is not None:
        raise ValidationError(
            {"change_request": "Change request has already been committed."}
        )
    if not environment.use_v2_feature_versioning:
        raise ValidationError(
            {"environment": "Environment must use v2 feature versioning."}
        )


def _stage_flag_change(
    *,
    environment: Environment,
    feature: Feature,
    change_request: ChangeRequest,
    apply: Callable[[_FlagState], _FlagState],
    overwrite_system_segment_overrides: bool,
) -> None:
    """Record a flag change on a change request, rather than making it live.

    The change set stores the difference from the live flag, so publishing the change
    request applies it and checks it for conflicts with changes published since.
    """
    _validate_change_request(environment, change_request)

    with transaction.atomic():
        change_set, _ = VersionChangeSet.objects.select_for_update().get_or_create(
            change_request=change_request,
            feature=feature,
            defaults={"live_from": change_request.live_from},
        )
        live = _get_live_flag_state(environment, feature)
        staged = apply(_get_staged_flag_state(change_set, live))
        _check_staged_priorities(staged.overrides.values())

        created_segment_ids = [
            segment_id
            for segment_id in staged.overrides
            if segment_id not in live.overrides
        ]
        updated_segment_ids = [
            segment_id
            for segment_id, feature_state in staged.overrides.items()
            if segment_id in live.overrides
            and feature_state != live.overrides[segment_id]
        ]
        deleted_segment_ids = [
            segment_id
            for segment_id in live.overrides
            if segment_id not in staged.overrides
        ]
        if not overwrite_system_segment_overrides and exceeds_segment_override_limit(
            environment,
            segment_ids_to_create_overrides=created_segment_ids,
            segment_ids_to_delete_overrides=deleted_segment_ids,
            exclusive=True,
        ):
            raise ValidationError(
                {"segment_overrides": [SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE]}
            )

        environment_default_updated = (
            staged.environment_default != live.environment_default
        )
        feature_states_to_update = [
            *([staged.environment_default] if environment_default_updated else []),
            *(staged.overrides[segment_id] for segment_id in updated_segment_ids),
        ]
        change_set.feature_states_to_create = json.dumps(
            [staged.overrides[segment_id] for segment_id in created_segment_ids]
        )
        change_set.feature_states_to_update = json.dumps(feature_states_to_update)
        change_set.segment_ids_to_delete_overrides = json.dumps(deleted_segment_ids)
        change_set.save(
            update_fields=[
                "feature_states_to_create",
                "feature_states_to_update",
                "segment_ids_to_delete_overrides",
            ]
        )

    logger.info(
        "flag.staged",
        organisation__id=environment.project.organisation_id,
        project__id=environment.project_id,
        environment__id=environment.id,
        feature__id=feature.id,
        change_request__id=change_request.id,
        environment_default__updated=environment_default_updated,
        segment_overrides__created__segment__ids=created_segment_ids,
        segment_overrides__updated__segment__ids=updated_segment_ids,
        segment_overrides__deleted__segment__ids=deleted_segment_ids,
    )


def update_flag(
    *,
    environment: Environment,
    feature: Feature,
    changes: UpdateFlagRequest,
    replace: bool,
    author: AuthorData,
    change_request: ChangeRequest | None = None,
    overwrite_system_segment_overrides: bool,
) -> UpdateFlagResponse:
    """Write the given parts of a flag, whichever versioning the environment uses.

    Overrides of system segments can only be changed by passing
    `overwrite_system_segment_overrides=True`.
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

    if change_request is not None:
        _stage_flag_change(
            environment=environment,
            feature=feature,
            change_request=change_request,
            apply=lambda staged: _apply_flag_update(
                staged,
                changes,
                replace=replace,
                overwrite_system_segment_overrides=overwrite_system_segment_overrides,
            ),
            overwrite_system_segment_overrides=overwrite_system_segment_overrides,
        )
        return get_flag(environment=environment, feature=feature)

    segments = _OverriddenSegments([], [], [])

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
            segments = _write_segment_overrides(
                environment=environment,
                feature=feature,
                version=version,
                environment_default=environment_default,
                overrides=_get_overrides_by_segment_id(feature_states),
                changes=override_changes,
                replace=replace,
                overwrite_system_segment_overrides=overwrite_system_segment_overrides,
            )

        if version is not None:
            version.publish(
                published_by=author.user, published_by_api_key=author.api_key
            )

        for segment in Segment.objects.filter(id__in=segments.created):
            validate_segment_flag_dependencies(segment)
        report_flag_dependency_changes(
            environment=environment,
            feature=feature,
            created_segment_ids=segments.created,
            deleted_segment_ids=segments.deleted,
            author=author,
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
    change_request: ChangeRequest | None = None,
    overwrite_system_segment_overrides: bool,
) -> UpdateFlagResponse:
    """Remove a flag's override for one segment, leaving the rest of the flag alone.

    Overrides of system segments can only be removed by passing
    `overwrite_system_segment_overrides=True`.
    """
    if change_request is not None:
        _stage_flag_change(
            environment=environment,
            feature=feature,
            change_request=change_request,
            apply=lambda staged: _apply_segment_override_deletion(
                staged,
                segment_id,
                overwrite_system_segment_overrides=overwrite_system_segment_overrides,
            ),
            overwrite_system_segment_overrides=overwrite_system_segment_overrides,
        )
        return get_flag(environment=environment, feature=feature)

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

        report_flag_dependency_changes(
            environment=environment,
            feature=feature,
            created_segment_ids=[],
            deleted_segment_ids=[segment_id],
            author=author,
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
