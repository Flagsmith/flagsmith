import datetime
import logging
from collections.abc import Iterable
from itertools import chain
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, TypeVar, cast
from uuid import UUID

from common.core.utils import using_database_replica
from django.utils import timezone
from flag_engine.context import types as engine_types
from flag_engine.segments.types import ConditionOperator, RuleType
from pydantic import TypeAdapter

from environments.constants import IDENTITY_INTEGRATIONS_RELATION_NAMES
from features.versioning.models import EnvironmentFeatureVersion, VersionChangeSet
from segments.types import SegmentEngineMetadata
from util.engine_models.environments.integrations.models import IntegrationModel
from util.engine_models.environments.models import (
    EnvironmentAPIKeyModel,
    EnvironmentModel,
    WebhookModel,
)
from util.engine_models.features.models import (
    FeatureModel,
    FeatureSegmentModel,
    FeatureStateModel,
    MultivariateFeatureOptionModel,
    MultivariateFeatureStateValueModel,
    ScheduledChangeModel,
)
from util.engine_models.identities.models import IdentityModel
from util.engine_models.identities.traits.models import TraitModel
from util.engine_models.organisations.models import OrganisationModel
from util.engine_models.projects.models import ProjectModel
from util.engine_models.segments.models import (
    SegmentConditionModel,
    SegmentModel,
    SegmentRuleModel,
)

if TYPE_CHECKING:  # pragma: no cover
    from environments.identities.models import (  # type: ignore[attr-defined]
        Identity,
        Trait,
    )
    from environments.models import Environment, EnvironmentAPIKey
    from features.models import Feature, FeatureSegment, FeatureState
    from features.multivariate.models import (
        MultivariateFeatureOption,
        MultivariateFeatureStateValue,
    )
    from integrations.common.models import EnvironmentIntegrationModel
    from integrations.webhook.models import WebhookConfiguration
    from organisations.models import Organisation
    from projects.models import Project
    from segments.models import Condition, Segment, SegmentRule


logger = logging.getLogger(__name__)


__all__ = (
    "map_condition_to_segment_condition",
    "map_environment_api_key_to_engine",
    "map_environment_to_engine",
    "map_feature_to_engine",
    "map_identity_to_engine",
    "map_environment_to_evaluation_context",
    "map_mv_option_to_engine",
    "map_rule_to_segment_rule",
    "map_segment_to_engine",
    "map_segment_to_segment_context",
    "map_traits_to_engine",
)


def map_traits_to_engine(traits: Iterable["Trait"]) -> list[TraitModel]:
    return [
        TraitModel(trait_key=trait.trait_key, trait_value=trait.trait_value)
        for trait in traits
    ]


def map_segment_to_engine(
    segment: "Segment",
) -> SegmentModel:
    segment_rules = segment.rules.all()

    # No reading from ORM past this point!

    return SegmentModel(
        id=segment.pk,
        name=segment.name,
        rules=[
            map_segment_rule_to_engine(segment_rule) for segment_rule in segment_rules
        ],
    )


def map_segment_rule_to_engine(
    segment_rule: "SegmentRule",
) -> SegmentRuleModel:
    segment_sub_rules = segment_rule.rules.all()
    conditions = segment_rule.conditions.all()

    return SegmentRuleModel(
        type=segment_rule.type,  # type: ignore[arg-type]
        rules=[
            map_segment_rule_to_engine(segment_sub_rule)
            for segment_sub_rule in segment_sub_rules
        ],
        conditions=[
            SegmentConditionModel(
                operator=condition.operator,  # type: ignore[arg-type]
                value=condition.value,
                property_=condition.property,
            )
            for condition in conditions
        ],
    )


def map_integration_to_engine(
    integration: Optional["EnvironmentIntegrationModel"],
) -> Optional[IntegrationModel]:
    if not integration:
        return None
    return IntegrationModel(
        api_key=integration.api_key,
        base_url=integration.base_url,
        entity_selector=getattr(integration, "entity_selector", None),
    )


def map_webhook_config_to_engine(
    webhook_config: Optional["WebhookConfiguration"],
) -> Optional[WebhookModel]:
    if not webhook_config:
        return None
    return WebhookModel(
        url=webhook_config.url,
        secret=webhook_config.secret,
    )


def _get_effective_live_from(
    feature_state: "FeatureState",
) -> Optional[datetime.datetime]:
    """
    Resolve `live_from` consistently across both versioning systems.

    V1 (legacy): the timestamp lives directly on the FeatureState.
    V2 (`use_v2_feature_versioning`): it lives on the linked
    EnvironmentFeatureVersion instead — FeatureState.live_from isn't
    guaranteed to be populated there.

    Mirrors the branching already used by `FeatureState.is_live`, which
    doesn't expose this comparison as a reusable, version-agnostic helper.
    """
    if feature_state.environment_feature_version_id is not None:
        environment_feature_version = feature_state.environment_feature_version
        return (
            environment_feature_version.live_from
            if environment_feature_version
            else None
        )
    return feature_state.live_from


def _is_scheduled_change_locked_in(feature_state: "FeatureState") -> bool:
    """
    Whether a not-yet-live feature state is actually committed to going
    live, mirroring the publication half of `FeatureState.is_live`'s V1/V2
    branching (`_get_effective_live_from` mirrors its timestamp half).

    A future `live_from` alone doesn't mean "scheduled":

    V2: `live_from` is writable on an *unpublished* EnvironmentFeatureVersion
    (the versioning API accepts it at draft-create time), so its auto-cloned
    feature states carry a future timestamp before anyone decides to publish.
    Require `published_at` to be set.

    V1: feature states belonging to an uncommitted change request have
    `version=None` but already carry their target `live_from`. Require a
    real version number.

    Either way, a draft isn't locked in yet and must not be advertised to
    SDKs as a scheduled change (matching the committed-only filter the
    VersionChangeSet mechanism applies).
    """
    if feature_state.environment_feature_version_id is not None:
        environment_feature_version = feature_state.environment_feature_version
        # `select_related` joins straight onto the FK column, bypassing
        # `EnvironmentFeatureVersion`'s soft-delete manager — a cancelled
        # (soft-deleted) version can still come back here, so `deleted_at`
        # must be checked explicitly rather than relying on the manager.
        return (
            environment_feature_version is not None
            and environment_feature_version.published_at is not None
            and environment_feature_version.deleted_at is None
        )
    return feature_state.version is not None


def _parse_changeset_feature_state_value(
    value_dict: object,
) -> object:
    if not isinstance(value_dict, dict):
        return None
    for key in ("string_value", "integer_value", "boolean_value"):
        value = value_dict.get(key)
        if value is not None:
            return value
    return None


def _get_valid_changeset_entries(
    change_set: VersionChangeSet,
    field_name: str,
    *,
    feature_segment_required: bool,
) -> List[Dict[str, object]]:
    """
    `feature_states_to_create`/`feature_states_to_update` store
    `json.dumps()` of *raw client JSON* at CR-create time — that JSON is only
    validated at publish time (`features/versioning/tasks.py`). This
    parser runs on the SDK hot read path (the environment-document endpoint),
    so a malformed blob must degrade to "skip and log", never propagate: one
    garbage changeset must not 500 the document build — nor hide scheduled
    changes for the environment's other, well-formed changesets.
    """
    try:
        entries = getattr(change_set, f"get_parsed_{field_name}")()
    except (ValueError, TypeError) as exc:
        logger.warning(
            "Skipping unparseable %s JSON on VersionChangeSet id=%s "
            "(feature id=%s, change request id=%s): %s",
            field_name,
            change_set.id,
            change_set.feature_id,
            change_set.change_request_id,
            exc,
        )
        return []
    if not isinstance(entries, list):
        logger.warning(
            "Skipping %s on VersionChangeSet id=%s (feature id=%s, change "
            "request id=%s): expected a JSON list, got %s",
            field_name,
            change_set.id,
            change_set.feature_id,
            change_set.change_request_id,
            type(entries).__name__,
        )
        return []
    return [
        entry
        for entry in entries
        if _is_valid_changeset_entry(
            entry,
            change_set,
            field_name,
            feature_segment_required=feature_segment_required,
        )
    ]


def _is_valid_changeset_entry(
    entry: object,
    change_set: VersionChangeSet,
    field_name: str,
    *,
    feature_segment_required: bool,
) -> bool:
    """
    Shape-check a single changeset feature-state entry so the caller can use
    plain subscripts safely. `enabled` is genuinely optional client-side (the
    upstream serializer leaves it to a model default), so its absence here is
    an expected malformed-at-rest shape, not a can't-happen guard.
    """

    def _skip(reason: str) -> bool:
        logger.warning(
            "Skipping malformed %s entry on VersionChangeSet id=%s "
            "(feature id=%s, change request id=%s): %s",
            field_name,
            change_set.id,
            change_set.feature_id,
            change_set.change_request_id,
            reason,
        )
        return False

    if not isinstance(entry, dict):
        return _skip(f"expected an object, got {type(entry).__name__}")
    if not isinstance(entry.get("enabled"), bool):
        return _skip("missing or non-boolean 'enabled'")
    feature_state_value = entry.get("feature_state_value")
    if feature_state_value is not None and not isinstance(feature_state_value, dict):
        return _skip("'feature_state_value' is not an object")
    feature_segment = entry.get("feature_segment")
    if feature_segment is None:
        if feature_segment_required:
            return _skip("missing 'feature_segment'")
        return True
    if not isinstance(feature_segment, dict):
        return _skip("'feature_segment' is not an object")
    segment_id = feature_segment.get("segment")
    if not isinstance(segment_id, int) or isinstance(segment_id, bool):
        return _skip("'feature_segment.segment' is not an integer")
    return True


_ScheduledChangeKeyT = TypeVar("_ScheduledChangeKeyT")


def _keep_earliest_scheduled_change(
    by_key: Dict[_ScheduledChangeKeyT, ScheduledChangeModel],
    key: _ScheduledChangeKeyT,
    candidate: ScheduledChangeModel,
) -> None:
    existing = by_key.get(key)
    if existing is None or candidate.live_from < existing.live_from:
        by_key[key] = candidate


def _get_pending_version_change_set_scheduled_changes(
    environment: "Environment",
) -> Tuple[
    Dict[int, ScheduledChangeModel], Dict[Tuple[int, int], ScheduledChangeModel]
]:
    """
    Change-request-driven scheduled changes are staged
    as a `VersionChangeSet` (a JSON diff of the change request) rather than
    a real FeatureState row. A background task only materialises the actual
    FeatureState/EnvironmentFeatureVersion at `live_from`, so between commit
    and go-live there is nothing for `_get_prioritised_feature_states` to
    find. This reads those pending diffs directly.

    Only changesets tied to an already-*committed* change request are
    surfaced — a change still in draft/review isn't locked in yet and
    shouldn't be advertised to SDKs as a scheduled change.

    Returns a 2-tuple: (environment-default changes by feature id,
    segment-override changes by (feature id, segment id)).
    """
    environment_default_by_feature_id: Dict[int, ScheduledChangeModel] = {}
    segment_override_by_feature_and_segment_id: Dict[
        Tuple[int, int], ScheduledChangeModel
    ] = {}

    # `change_request__...` is a JOIN condition, not a query through
    # ChangeRequest's own soft-delete manager — a soft-deleted change
    # request would still match here unless excluded explicitly.
    pending_change_sets = using_database_replica(VersionChangeSet.objects).filter(
        environment=environment,
        published_at__isnull=True,
        live_from__isnull=False,
        live_from__gt=timezone.now(),
        change_request__committed_at__isnull=False,
        change_request__deleted_at__isnull=True,
    )

    for change_set in pending_change_sets:
        # The changeset JSON is raw, publish-time-validated client input —
        # `_get_valid_changeset_entries` shape-checks every entry (skipping
        # and logging bad ones), so the subscripts below can't raise.
        for fs_update in _get_valid_changeset_entries(
            change_set, "feature_states_to_update", feature_segment_required=False
        ):
            candidate = ScheduledChangeModel(
                live_from=change_set.live_from,
                enabled=bool(fs_update["enabled"]),
                feature_state_value=_parse_changeset_feature_state_value(
                    fs_update.get("feature_state_value")
                ),
            )
            feature_segment = fs_update.get("feature_segment")
            if feature_segment is None:
                _keep_earliest_scheduled_change(
                    environment_default_by_feature_id,
                    change_set.feature_id,
                    candidate,
                )
            else:
                segment_id = cast(Dict[str, object], feature_segment)["segment"]
                _keep_earliest_scheduled_change(
                    segment_override_by_feature_and_segment_id,
                    (change_set.feature_id, cast(int, segment_id)),
                    candidate,
                )

        # feature states to create are always segment overrides — an
        # environment default always already exists, so it's updated,
        # never created. Hence `feature_segment_required`.
        for fs_create in _get_valid_changeset_entries(
            change_set, "feature_states_to_create", feature_segment_required=True
        ):
            feature_segment = cast(Dict[str, object], fs_create["feature_segment"])
            candidate = ScheduledChangeModel(
                live_from=change_set.live_from,
                enabled=bool(fs_create["enabled"]),
                feature_state_value=_parse_changeset_feature_state_value(
                    fs_create.get("feature_state_value")
                ),
            )
            _keep_earliest_scheduled_change(
                segment_override_by_feature_and_segment_id,
                (change_set.feature_id, cast(int, feature_segment["segment"])),
                candidate,
            )

    return environment_default_by_feature_id, segment_override_by_feature_and_segment_id


def map_feature_state_to_engine(
    feature_state: "FeatureState",
    *,
    mv_fs_values: Optional[Iterable["MultivariateFeatureStateValue"]] = None,
    scheduled_feature_state: Optional["FeatureState"] = None,
    scheduled_change_override: Optional[ScheduledChangeModel] = None,
) -> FeatureStateModel:
    feature = feature_state.feature
    feature_segment: Optional["FeatureSegment"] = feature_state.feature_segment

    if feature_segment:
        feature_segment_model = FeatureSegmentModel(
            priority=feature_segment.priority,
        )
    else:
        feature_segment_model = None

    # Surface the next not-yet-live version of this feature state, if the
    # caller opted in and one exists. Without opting in, non-live feature
    # states are never mapped at all.
    scheduled_change_model: Optional[ScheduledChangeModel] = None
    if scheduled_feature_state is not None:
        scheduled_live_from = _get_effective_live_from(scheduled_feature_state)
        if scheduled_live_from is not None:
            scheduled_change_model = ScheduledChangeModel(
                live_from=scheduled_live_from,
                enabled=scheduled_feature_state.enabled,
                feature_state_value=scheduled_feature_state.get_feature_state_value(),
            )

    # A change-request-scheduled change has no
    # FeatureState row yet — it's staged as a VersionChangeSet JSON diff
    # until a background task materialises it at `live_from`. The caller
    # resolves that from `_get_pending_version_change_set_scheduled_changes`
    # and passes the winner here, since there's no ORM object to compare
    # against `scheduled_feature_state` this deep in the call stack.
    if scheduled_change_override is not None and (
        scheduled_change_model is None
        or scheduled_change_override.live_from < scheduled_change_model.live_from
    ):
        scheduled_change_model = scheduled_change_override

    return FeatureStateModel(
        enabled=feature_state.enabled,
        django_id=feature_state.pk,
        feature_state_value=feature_state.get_feature_state_value(),
        featurestate_uuid=feature_state.uuid,
        feature_segment=feature_segment_model,
        feature=map_feature_to_engine(feature),
        multivariate_feature_state_values=[  # type: ignore[arg-type]
            map_mv_fs_value_to_engine(mv_fs_value) for mv_fs_value in mv_fs_values or []
        ],
        scheduled_change=scheduled_change_model,
    )


def map_mv_fs_value_to_engine(
    mv_fs_value: "MultivariateFeatureStateValue",
) -> MultivariateFeatureStateValueModel:
    mv_feature_option: "MultivariateFeatureOption" = (
        mv_fs_value.multivariate_feature_option
    )

    return MultivariateFeatureStateValueModel(
        percentage_allocation=mv_fs_value.percentage_allocation,
        id=mv_fs_value.id,
        mv_fs_value_uuid=mv_fs_value.uuid,
        multivariate_feature_option=map_mv_option_to_engine(mv_feature_option),
    )


def map_feature_to_engine(feature: "Feature") -> FeatureModel:
    return FeatureModel(id=feature.pk, name=feature.name, type=feature.type)


def map_mv_option_to_engine(
    mv_option: "MultivariateFeatureOption",
) -> MultivariateFeatureOptionModel:
    return MultivariateFeatureOptionModel(
        value=mv_option.value, id=mv_option.id, key=mv_option.key
    )


def map_environment_to_engine(
    environment: "Environment",
    *,
    with_integrations: bool = True,
    include_scheduled: bool = False,
) -> EnvironmentModel:
    """
    Maps Core API's `environments.models.Environment` model instance to the
    flag_engine environment document.
    Before building the document, takes care of resolving relationships and
    feature versions.

    :param Environment environment: the environment to map
    :param include_scheduled: opt-in. When True, each returned
        FeatureStateModel additionally carries a `scheduled_change` field
        describing the next not-yet-live version of that feature state, if
        any. Defaults to False, in which case the response shape is
        unchanged.

        Known limitations — shapes of genuinely scheduled change that are
        *not* surfaced (a consumer cannot distinguish "nothing scheduled"
        from "scheduled, but in an unsupported shape"):

        * v2 segment overrides via the versioning flow: a future *published*
          EnvironmentFeatureVersion's segment overrides hang off that
          version's own FeatureSegment clones, which the
          `latest_environment_feature_version_uuids` filter in
          `_get_segment_feature_states` excludes before the scheduled scan
          ever sees them. The FeatureState-based mechanism therefore covers
          v2 environment defaults and V1 feature states (any scope), but
          never v2 segment overrides.
        * Brand-new segment overrides staged in a changeset
          (`feature_states_to_create`): there is no live FeatureStateModel
          to attach the `scheduled_change` to until the override exists —
          see the test docstring on
          `test_include_scheduled__surfaces_pending_update_to_existing_segment_override`
          in `tests/unit/util/mappers/test_scheduled_changes.py`.
        * Scheduled deletions: `segment_ids_to_delete_overrides` in a
          committed changeset is never read, so a scheduled *removal* of a
          segment override surfaces nothing.
        * Multivariate values: `ScheduledChangeModel` carries only `enabled`
          and the control `feature_state_value` — a scheduled change to MV
          weights alone advertises no meaningful diff.
        * Identity overrides: effectively V1-only. v2 identity feature
          states are always live, so the `include_scheduled` threading
          through `map_identity_to_engine` rarely has anything to surface
          under v2.
    :rtype EnvironmentModel
    """
    project: "Project" = environment.project
    organisation: "Organisation" = project.organisation

    # Read relationships - grab all the data needed from the ORM here.

    project_segments = [
        ps for ps in project.segments.all() if ps.id == ps.version_of_id
    ]

    (
        project_segment_feature_states_by_segment_id,
        project_segment_scheduled_by_segment_id,
    ) = _get_segment_feature_states(
        project_segments,
        environment.pk,
        latest_environment_feature_version_uuids=(
            {
                efv.uuid
                for efv in EnvironmentFeatureVersion.objects.get_latest_versions_by_environment_id(
                    environment.id
                )
            }
            if environment.use_v2_feature_versioning
            else []
        ),
        include_scheduled=include_scheduled,
    )
    # Drop feature-specific segments that have no FeatureSegment in this
    # environment — without one, they have no evaluation path here, and
    # their rules only inflate the environment document.
    project_segments = [
        ps
        for ps in project_segments
        if ps.feature_id is None
        or project_segment_feature_states_by_segment_id.get(ps.pk)
    ]
    project_segment_rules_by_segment_id: Dict[
        int,
        Iterable["SegmentRule"],
    ] = {segment.pk: segment.rules.all() for segment in project_segments}
    environment_feature_states, environment_scheduled_by_feature_id = (
        _get_prioritised_feature_states(
            [
                feature_state
                for feature_state in environment.feature_states.all()
                if feature_state.feature_segment_id is None
                and feature_state.identity_id is None
            ],
            include_scheduled=include_scheduled,
        )
    )
    all_environment_feature_states = (
        *environment_feature_states,
        *chain(*project_segment_feature_states_by_segment_id.values()),
    )
    multivariate_feature_state_values_by_feature_state_id = {
        feature_state.pk: feature_state.multivariate_feature_state_values.all()
        for feature_state in all_environment_feature_states
    }

    # Change-request-scheduled changes have no
    # FeatureState row yet — see `_get_pending_version_change_set_scheduled_changes`.
    (
        changeset_environment_default_by_feature_id,
        changeset_segment_override_by_feature_and_segment_id,
    ) = (
        _get_pending_version_change_set_scheduled_changes(environment)
        if include_scheduled
        else ({}, {})
    )

    # Read integrations.
    integration_configs: dict[
        str, "EnvironmentIntegrationModel | WebhookConfiguration | None"
    ] = {}
    if with_integrations:
        for attr_name in IDENTITY_INTEGRATIONS_RELATION_NAMES:
            integration_config = getattr(environment, attr_name, None)
            if integration_config and not integration_config.deleted:
                integration_configs[attr_name] = integration_config

    # No reading from ORM past this point!

    # Prepare relationships.
    organisation_model = OrganisationModel(
        id=organisation.pk,
        name=organisation.name,
        feature_analytics=organisation.feature_analytics,
        stop_serving_flags=organisation.stop_serving_flags,
        persist_trait_data=organisation.persist_trait_data,
    )
    project_segment_models = [
        SegmentModel(
            id=segment.pk,
            name=segment.name,
            rules=[
                map_segment_rule_to_engine(segment_rule)
                for segment_rule in project_segment_rules_by_segment_id.pop(segment.pk)
            ],
            feature_states=[
                map_feature_state_to_engine(
                    feature_state,
                    mv_fs_values=multivariate_feature_state_values_by_feature_state_id.pop(
                        feature_state.pk,
                    ),
                    scheduled_feature_state=project_segment_scheduled_by_segment_id.get(
                        segment.pk, {}
                    ).get(feature_state.feature_id),
                    scheduled_change_override=changeset_segment_override_by_feature_and_segment_id.get(
                        (feature_state.feature_id, segment.pk)
                    ),
                )
                for feature_state in project_segment_feature_states_by_segment_id.pop(
                    segment.pk
                )
            ],
        )
        for segment in project_segments
    ]
    project_model = ProjectModel(
        id=project.pk,
        name=project.name,
        hide_disabled_flags=project.hide_disabled_flags,
        enable_realtime_updates=project.enable_realtime_updates,
        server_key_only_feature_ids=[
            feature.pk
            for feature_state in environment_feature_states
            if (feature := feature_state.feature).is_server_key_only
        ],
        organisation=organisation_model,
        segments=project_segment_models,
    )
    feature_state_models = [
        map_feature_state_to_engine(
            feature_state,
            mv_fs_values=multivariate_feature_state_values_by_feature_state_id.pop(
                feature_state.pk,
            ),
            scheduled_feature_state=environment_scheduled_by_feature_id.get(
                feature_state.feature_id
            ),
            scheduled_change_override=changeset_environment_default_by_feature_id.get(
                feature_state.feature_id
            ),
        )
        for feature_state in environment_feature_states
    ]

    # Prepare integrations.
    amplitude_config_model = map_integration_to_engine(
        integration_configs.pop("amplitude_config", None),
    )
    heap_config_model = map_integration_to_engine(
        integration_configs.pop("heap_config", None),
    )
    mixpanel_config_model = map_integration_to_engine(
        integration_configs.pop("mixpanel_config", None),
    )
    rudderstack_config_model = map_integration_to_engine(
        integration_configs.pop("rudderstack_config", None),
    )
    segment_config_model = map_integration_to_engine(
        integration_configs.pop("segment_config", None),
    )
    webhook_config_model = map_webhook_config_to_engine(
        integration_configs.pop("webhook_config", None),
    )

    return EnvironmentModel(
        #
        # Attributes:
        id=environment.pk,
        api_key=environment.api_key,
        name=environment.name,
        allow_client_traits=environment.allow_client_traits,
        updated_at=environment.updated_at,
        use_identity_composite_key_for_hashing=environment.use_identity_composite_key_for_hashing,
        hide_sensitive_data=environment.hide_sensitive_data,
        hide_disabled_flags=environment.hide_disabled_flags,
        use_identity_overrides_in_local_eval=environment.use_identity_overrides_in_local_eval,
        #
        # Relationships:
        project=project_model,
        feature_states=feature_state_models,
        #
        # Integrations:
        amplitude_config=amplitude_config_model,
        heap_config=heap_config_model,
        mixpanel_config=mixpanel_config_model,
        rudderstack_config=rudderstack_config_model,
        segment_config=segment_config_model,
        webhook_config=webhook_config_model,
    )


def map_environment_api_key_to_engine(
    environment_api_key: "EnvironmentAPIKey",
) -> EnvironmentAPIKeyModel:
    client_api_key = environment_api_key.environment.api_key

    return EnvironmentAPIKeyModel(
        id=environment_api_key.pk,
        key=environment_api_key.key,
        created_at=environment_api_key.created_at,
        name=environment_api_key.name,
        client_api_key=client_api_key,
        expires_at=environment_api_key.expires_at,
        active=environment_api_key.active,
    )


def map_identity_to_engine(
    identity: "Identity",
    *,
    with_overrides: bool = True,
    with_traits: bool = True,
    include_scheduled: bool = False,
) -> IdentityModel:
    environment_api_key = identity.environment.api_key

    # Read relationships - grab all the data needed from the ORM here.
    if with_overrides:
        identity_feature_states, identity_scheduled_by_feature_id = (
            _get_prioritised_feature_states(
                identity.identity_features.all(),
                include_scheduled=include_scheduled,
            )
        )
        multivariate_feature_state_values_by_feature_state_id = {
            feature_state.pk: feature_state.multivariate_feature_state_values.all()
            for feature_state in identity_feature_states
        }
    else:
        identity_feature_states = []
        identity_scheduled_by_feature_id = {}
        multivariate_feature_state_values_by_feature_state_id = {}

    identity_traits: Iterable["Trait"] = (
        identity.identity_traits.all() if with_traits else []
    )

    # Prepare relationships.
    identity_feature_state_models = [
        map_feature_state_to_engine(
            feature_state,
            mv_fs_values=multivariate_feature_state_values_by_feature_state_id.pop(
                feature_state.pk,
            ),
            scheduled_feature_state=identity_scheduled_by_feature_id.get(
                feature_state.feature_id
            ),
        )
        for feature_state in identity_feature_states
    ]
    identity_trait_models = map_traits_to_engine(identity_traits)

    return IdentityModel(
        # Attributes:
        identifier=identity.identifier,
        environment_api_key=environment_api_key,
        created_date=identity.created_date,
        django_id=identity.pk,
        #
        # Relationships:
        identity_features=identity_feature_state_models,  # type: ignore[arg-type]
        identity_traits=identity_trait_models,
    )


_rule_type_adapter: TypeAdapter[RuleType] = TypeAdapter(RuleType)
_condition_operator_adapter: TypeAdapter[ConditionOperator] = TypeAdapter(
    ConditionOperator
)


def map_environment_to_evaluation_context(
    *,
    environment: "Environment",
    identity: "Identity | None" = None,
    traits: "Iterable[Trait] | None" = None,
    segments: "Iterable[Segment] | None" = None,
) -> "engine_types.EvaluationContext[SegmentEngineMetadata, object]":
    """Map Django ORM Environment (and optionally Identity) to a flag-engine EvaluationContext."""
    context: engine_types.EvaluationContext[SegmentEngineMetadata, object] = {
        "environment": {
            "key": environment.api_key,
            "name": environment.name or "",
        },
    }
    if identity is not None:
        trait_items: "Iterable[Trait]" = (
            traits if traits is not None else identity.identity_traits.all()
        )
        context["identity"] = {
            "identifier": identity.identifier,
            "key": identity.get_hash_key(
                environment.use_identity_composite_key_for_hashing
            ),
            "traits": {trait.trait_key: trait.trait_value for trait in trait_items},
        }
    if segments is not None:
        context["segments"] = {
            str(segment.pk): map_segment_to_segment_context(segment)
            for segment in segments
        }
    return context


def map_segment_to_segment_context(
    segment: "Segment",
) -> "engine_types.SegmentContext[SegmentEngineMetadata, object]":
    """Map a Django ORM Segment to a flag-engine SegmentContext TypedDict."""
    return {
        "key": str(segment.pk),
        "name": segment.name,
        "rules": [map_rule_to_segment_rule(rule) for rule in segment.rules.all()],
        "metadata": SegmentEngineMetadata(pk=segment.pk),
    }


def map_rule_to_segment_rule(rule: "SegmentRule") -> engine_types.SegmentRule:
    return {
        "type": _rule_type_adapter.validate_python(rule.type),
        "conditions": [
            map_condition_to_segment_condition(condition)
            for condition in rule.conditions.all()
        ],
        "rules": [map_rule_to_segment_rule(sub_rule) for sub_rule in rule.rules.all()],
    }


def map_condition_to_segment_condition(
    condition: "Condition",
) -> engine_types.StrValueSegmentCondition:
    return {
        "property": condition.property or "",
        "operator": _condition_operator_adapter.validate_python(condition.operator),
        "value": condition.value or "",
    }


def _get_prioritised_feature_states(
    feature_states: Iterable["FeatureState"],
    *,
    include_scheduled: bool = False,
) -> Tuple[List["FeatureState"], Dict[int, "FeatureState"]]:
    """
    Returns a 2-tuple of (prioritised live feature states, next-scheduled
    feature state by feature id).

    The second element is only ever populated when
    `include_scheduled=True`. When it's not, non-live
    feature states (including future-scheduled ones) are silently discarded
    with no way to recover them from this function's result.
    """
    prioritised_feature_state_by_feature_id = {}  # type: ignore[var-annotated]
    scheduled_feature_state_by_feature_id: Dict[int, "FeatureState"] = {}
    for feature_state in feature_states:
        # TODO: this call to is_live was causing an N+1 issue.
        #  For now, we have solved it with an extra select_related, but
        #  there is probably a neater solution here.
        if not feature_state.is_live:
            if include_scheduled and _is_scheduled_change_locked_in(feature_state):
                live_from = _get_effective_live_from(feature_state)
                if live_from is not None and live_from > timezone.now():
                    existing_scheduled = scheduled_feature_state_by_feature_id.get(
                        feature_state.feature_id
                    )
                    if existing_scheduled is None or live_from < (
                        _get_effective_live_from(existing_scheduled) or live_from
                    ):
                        scheduled_feature_state_by_feature_id[
                            feature_state.feature_id
                        ] = feature_state
            continue
        if existing_feature_state := prioritised_feature_state_by_feature_id.get(
            feature_state.feature_id
        ):
            if existing_feature_state > feature_state:
                continue
        prioritised_feature_state_by_feature_id[feature_state.feature_id] = (
            feature_state
        )
    return (
        list(prioritised_feature_state_by_feature_id.values()),
        scheduled_feature_state_by_feature_id,
    )


def _get_segment_feature_states(
    segments: Iterable["Segment"],
    environment_id: int,
    latest_environment_feature_version_uuids: Iterable[UUID],
    *,
    include_scheduled: bool = False,
) -> Tuple[Dict[int, List["FeatureState"]], Dict[int, Dict[int, "FeatureState"]]]:
    feature_states_by_segment_id = {}  # type: ignore[var-annotated]
    scheduled_by_segment_id: Dict[int, Dict[int, "FeatureState"]] = {}

    for segment in segments:
        segment_feature_states = feature_states_by_segment_id.setdefault(segment.pk, [])
        segment_scheduled = scheduled_by_segment_id.setdefault(segment.pk, {})

        for feature_segment in segment.feature_segments.all():
            if feature_segment.environment_id != environment_id:
                continue

            if (
                latest_environment_feature_version_uuids
                and feature_segment.environment_feature_version_id  # type: ignore[operator]
                not in latest_environment_feature_version_uuids
            ):
                continue

            live_states, scheduled_states = _get_prioritised_feature_states(
                feature_segment.feature_states.all(),
                include_scheduled=include_scheduled,
            )
            segment_feature_states += live_states
            segment_scheduled.update(scheduled_states)

    return feature_states_by_segment_id, scheduled_by_segment_id
