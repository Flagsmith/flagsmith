from collections.abc import Iterable
from itertools import chain
from math import inf
from operator import attrgetter
from typing import TYPE_CHECKING, Dict, List, NamedTuple, Optional
from uuid import UUID

from django.db.models import Prefetch, Q
from flag_engine.context import types as engine_types
from flag_engine.segments.constants import IS_SET
from flag_engine.segments.types import ConditionOperator, RuleType
from pydantic import TypeAdapter

from environments.constants import IDENTITY_INTEGRATIONS_RELATION_NAMES
from evaluation.types import EvaluationContext, FeatureContext, SegmentContext
from features.types import FeatureEngineMetadata
from features.versioning.models import EnvironmentFeatureVersion
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


class MappedEvaluationContext(NamedTuple):
    context: EvaluationContext
    #: The feature states the context was built from, by id. Transitional — see
    #: `map_environment_to_evaluation_context`.
    feature_states_by_id: "dict[int, FeatureState]"


#: Context key and name of the synthetic segment carrying identity overrides.
#: Not a segment id — prefixed so it cannot collide with one.
IDENTITY_OVERRIDES_SEGMENT_KEY = "$identity_overrides"
IDENTITY_OVERRIDES_SEGMENT_NAME = "identity_overrides"

__all__ = (
    "MappedEvaluationContext",
    "map_condition_to_segment_condition",
    "map_environment_api_key_to_engine",
    "map_environment_to_engine",
    "map_feature_state_to_feature_context",
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


def map_feature_state_to_engine(
    feature_state: "FeatureState",
    *,
    mv_fs_values: Optional[Iterable["MultivariateFeatureStateValue"]] = None,
    metadata: Optional[dict[str, object]] = None,
) -> FeatureStateModel:
    feature = feature_state.feature
    feature_segment: Optional["FeatureSegment"] = feature_state.feature_segment

    if feature_segment:
        feature_segment_model = FeatureSegmentModel(
            priority=feature_segment.priority,
        )
    else:
        feature_segment_model = None

    return FeatureStateModel(
        metadata=metadata,
        enabled=feature_state.enabled,
        # The engine and SDKs seed multivariate variant allocation on django_id,
        # so feeding it the bucketing seed keeps variant assignment stable when
        # a feature state is recreated, without changing the engine model or
        # environment document schema. See issue #7913.
        django_id=feature_state.mv_hashing_seed,
        feature_state_value=feature_state.get_feature_state_value(),
        featurestate_uuid=feature_state.uuid,
        feature_segment=feature_segment_model,
        feature=map_feature_to_engine(feature),
        multivariate_feature_state_values=[  # type: ignore[arg-type]
            map_mv_fs_value_to_engine(mv_fs_value) for mv_fs_value in mv_fs_values or []
        ],
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
) -> EnvironmentModel:
    """
    Maps Core API's `environments.models.Environment` model instance to the
    flag_engine environment document.
    Before building the document, takes care of resolving relationships and
    feature versions.

    :param Environment environment: the environment to map
    :rtype EnvironmentModel
    """
    from experimentation.feature_state_metadata import (  # avoid circular import
        get_feature_state_metadata_builder,
    )

    project: "Project" = environment.project
    organisation: "Organisation" = project.organisation

    # Read relationships - grab all the data needed from the ORM here.

    get_feature_state_metadata = get_feature_state_metadata_builder(environment)

    project_segments = [
        ps for ps in project.segments.all() if ps.id == ps.version_of_id
    ]

    project_segment_feature_states_by_segment_id = _get_segment_feature_states(
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
    environment_feature_states: List["FeatureState"] = _get_prioritised_feature_states(
        [
            feature_state
            for feature_state in environment.feature_states.all()
            if feature_state.feature_segment_id is None
            and feature_state.identity_id is None
        ]
    )
    all_environment_feature_states = (
        *environment_feature_states,
        *chain(*project_segment_feature_states_by_segment_id.values()),
    )
    multivariate_feature_state_values_by_feature_state_id = {
        feature_state.pk: feature_state.multivariate_feature_state_values.all()
        for feature_state in all_environment_feature_states
    }

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
                    metadata=get_feature_state_metadata(feature_state),
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
            metadata=get_feature_state_metadata(feature_state),
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
        onboarding_pending=environment.first_evaluated_at is None,
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
) -> IdentityModel:
    environment_api_key = identity.environment.api_key

    # Read relationships - grab all the data needed from the ORM here.
    if with_overrides:
        identity_feature_states: List["FeatureState"] = _get_prioritised_feature_states(
            identity.identity_features.all(),
        )
        multivariate_feature_state_values_by_feature_state_id = {
            feature_state.pk: feature_state.multivariate_feature_state_values.all()
            for feature_state in identity_feature_states
        }
    else:
        identity_feature_states = []
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
    feature_name: str | None = None,
    additional_filters: "Q | None" = None,
) -> MappedEvaluationContext:
    """Map Django ORM models to a flag-engine `EvaluationContext`.

    Resolves the feature states that are current for `environment` — defaults,
    segment overrides, and `identity`'s own overrides — and lays them out as
    `$.features` plus the overrides carried on each segment.

    Returns those feature states alongside the context, keyed by id, so that
    callers still working in Django rows can map a `FlagResult` back to one via
    `metadata.feature_state_id`. That is scaffolding for the migration off
    `FeatureState.get_feature_state_value(identity=...)`; once serialisers read
    values off the result, only the context is needed.

    :param segments: segments to evaluate.
    """
    context: EvaluationContext = {
        "environment": {
            "key": environment.api_key,
            "name": environment.name or "",
        },
    }
    if identity is not None:
        trait_items: "Iterable[Trait]" = (
            traits
            if traits is not None
            # A transient identity was never persisted, so it has no stored
            # traits to read, and asking for them would raise.
            else identity.identity_traits.all()
            if identity.pk
            else ()
        )
        identity_traits = {trait.trait_key: trait.trait_value for trait in trait_items}
        if identity.system_traits:
            # System-owned traits are not user data: on a key clash, the system
            # value wins.
            identity_traits.update(identity.system_traits)
        context["identity"] = {
            "identifier": identity.identifier,
            "key": identity.get_hash_key(
                environment.use_identity_composite_key_for_hashing
            ),
            "traits": identity_traits,
        }

    (
        feature_states,
        features,
        identity_overrides,
        segment_overrides,
        mv_fs_values_by_feature_state_id,
    ) = _resolve_feature_states(
        environment=environment,
        identity=identity,
        feature_name=feature_name,
        additional_filters=additional_filters,
    )

    # No reading from ORM past this point!

    def to_feature_context(
        feature_state: "FeatureState",
        *,
        segment_id: int | None = None,
        priority: float | None = None,
    ) -> FeatureContext:
        return map_feature_state_to_feature_context(
            feature_state,
            mv_fs_values=mv_fs_values_by_feature_state_id.get(feature_state.pk),
            segment_id=segment_id,
            priority=priority,
        )

    if segments is not None:
        context["segments"] = {
            str(segment.pk): map_segment_to_segment_context(
                segment,
                overrides=[
                    to_feature_context(feature_state, segment_id=segment.pk)
                    for feature_state in segment_overrides.get(segment.pk) or ()
                ],
            )
            for segment in segments
        }

    if identity_overrides:
        # An identity override outranks every segment override, which the
        # engine expresses as a priority no segment can beat.
        context.setdefault("segments", {})[IDENTITY_OVERRIDES_SEGMENT_KEY] = (
            _map_identity_overrides_to_segment_context(
                [
                    to_feature_context(feature_state, priority=-inf)
                    for feature_state in identity_overrides
                ]
            )
        )

    context["features"] = {
        (feature_context := to_feature_context(feature_state))["name"]: feature_context
        for feature_state in features
    }

    return MappedEvaluationContext(
        context=context,
        feature_states_by_id={
            feature_state.pk: feature_state for feature_state in feature_states
        },
    )


class _ResolvedFeatureStates(NamedTuple):
    all: list["FeatureState"]
    #: Environment defaults, i.e. neither segment- nor identity-scoped.
    features: list["FeatureState"]
    identity_overrides: list["FeatureState"]
    segment_overrides: dict[int, list["FeatureState"]]
    mv_fs_values_by_feature_state_id: dict[
        int, "Iterable[MultivariateFeatureStateValue]"
    ]


def _resolve_feature_states(
    *,
    environment: "Environment",
    identity: "Identity | None",
    feature_name: str | None,
    additional_filters: "Q | None",
) -> _ResolvedFeatureStates:
    """Read the feature states current for `environment`, split by what they override."""
    # Deferred: `environments.models` imports this module's package.
    from features.multivariate.models import MultivariateFeatureStateValue
    from features.versioning.versioning_service import get_environment_flags_list

    override_filters = Q(identity__isnull=True)
    if identity is not None and identity.pk:
        # The identity is persisted (non-transient).
        # Look for its identity overrides in addition to segment overrides.
        override_filters = Q(identity=identity) | override_filters
    if additional_filters:
        override_filters &= additional_filters

    feature_states = get_environment_flags_list(
        environment=environment,
        feature_name=feature_name,
        additional_filters=override_filters,
        additional_select_related_args=["feature_segment__segment"],
        additional_prefetch_related_args=[
            Prefetch(
                "multivariate_feature_state_values",
                queryset=MultivariateFeatureStateValue.objects.select_related(
                    "multivariate_feature_option"
                ),
            )
        ],
    )

    resolved = _ResolvedFeatureStates(feature_states, [], [], {}, {})

    for feature_state in feature_states:
        resolved.mv_fs_values_by_feature_state_id[feature_state.pk] = (
            feature_state.multivariate_feature_state_values.all()
        )
        if feature_state.identity_id is not None:
            resolved.identity_overrides.append(feature_state)
        elif (feature_segment := feature_state.feature_segment) is not None:
            resolved.segment_overrides.setdefault(
                feature_segment.segment_id, []
            ).append(feature_state)
        else:
            resolved.features.append(feature_state)

    return resolved


def map_feature_state_to_feature_context(
    feature_state: "FeatureState",
    *,
    mv_fs_values: "Iterable[MultivariateFeatureStateValue] | None" = None,
    segment_id: int | None = None,
    priority: float | None = None,
) -> FeatureContext:
    """Map a Django ORM FeatureState to a flag-engine FeatureContext TypedDict."""
    feature = feature_state.feature
    metadata = FeatureEngineMetadata(
        feature_id=feature.pk,
        feature_state_id=feature_state.pk,
    )
    if segment_id is not None:
        metadata["segment_id"] = segment_id
    if feature_state.identity_id is not None:
        metadata["identity_id"] = feature_state.identity_id

    feature_context: FeatureContext = {
        # The engine seeds multivariate variant allocation on the feature
        # context key, so it has to be the bucketing seed rather than the
        # feature state id, or recreating a feature state would move every
        # enrolled identity to a different variant. See issue #7913.
        "key": str(feature_state.mv_hashing_seed),
        "name": feature.name,
        "enabled": feature_state.enabled,
        # Deliberately unparameterised by identity: picking a multivariate
        # value is the engine's job now.
        "value": feature_state.get_feature_state_value(),
        "metadata": metadata,
    }

    if variants := _map_mv_fs_values_to_feature_values(mv_fs_values or ()):
        feature_context["variants"] = variants

    if priority is not None:
        feature_context["priority"] = priority
    elif (feature_segment := feature_state.feature_segment) is not None:
        feature_context["priority"] = feature_segment.priority

    return feature_context


def _map_mv_fs_values_to_feature_values(
    mv_fs_values: "Iterable[MultivariateFeatureStateValue]",
) -> list[engine_types.FeatureValue]:
    # Ordered by id, and weighted by position in that order, because that is
    # the order Core API has always allocated percentages in. The engine
    # orders by `priority`, so the two only agree if we hand it the id order.
    feature_values: list[engine_types.FeatureValue] = []
    for index, mv_fs_value in enumerate(sorted(mv_fs_values, key=attrgetter("id"))):
        mv_option = mv_fs_value.multivariate_feature_option
        feature_value: engine_types.FeatureValue = {
            "value": mv_option.value,
            "weight": mv_fs_value.percentage_allocation,
            "priority": index,
        }
        if mv_option.key is not None:
            # An unkeyed option resolves to a null variant, as it does today.
            feature_value["key"] = mv_option.key
        feature_values.append(feature_value)
    return feature_values


def map_segment_to_segment_context(
    segment: "Segment",
    *,
    overrides: "list[FeatureContext] | None" = None,
) -> SegmentContext:
    """Map a Django ORM Segment to a flag-engine SegmentContext TypedDict."""
    segment_context: SegmentContext = {
        "key": str(segment.pk),
        "name": segment.name,
        "rules": [map_rule_to_segment_rule(rule) for rule in segment.rules.all()],
        "metadata": SegmentEngineMetadata(source="segment", pk=segment.pk),
    }
    if overrides:
        segment_context["overrides"] = overrides
    return segment_context


def _map_identity_overrides_to_segment_context(
    overrides: "list[FeatureContext]",
) -> SegmentContext:
    """Express identity overrides as a segment matching only that identity.

    The engine has no identity-override concept, so SDKs model them as a
    segment keyed on the identifier. Core API does the same, for one identity
    at a time — the identity being evaluated is the only one whose overrides
    are ever in the context.
    """
    return {
        "key": IDENTITY_OVERRIDES_SEGMENT_KEY,
        "name": IDENTITY_OVERRIDES_SEGMENT_NAME,
        "rules": [
            {
                "type": "ALL",
                "conditions": [
                    {
                        "property": "$.identity.key",
                        "operator": IS_SET,
                        "value": "",
                    }
                ],
            }
        ],
        "overrides": overrides,
        "metadata": SegmentEngineMetadata(source="identity_overrides"),
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
) -> List["FeatureState"]:
    prioritised_feature_state_by_feature_id = {}  # type: ignore[var-annotated]
    for feature_state in feature_states:
        # TODO: this call to is_live was causing an N+1 issue.
        #  For now, we have solved it with an extra select_related, but
        #  there is probably a neater solution here.
        if not feature_state.is_live:
            continue
        if existing_feature_state := prioritised_feature_state_by_feature_id.get(
            feature_state.feature_id
        ):
            if existing_feature_state > feature_state:
                continue
        prioritised_feature_state_by_feature_id[feature_state.feature_id] = (
            feature_state
        )
    return list(prioritised_feature_state_by_feature_id.values())


def _get_segment_feature_states(
    segments: Iterable["Segment"],
    environment_id: int,
    latest_environment_feature_version_uuids: Iterable[UUID],
) -> Dict[int, List["FeatureState"]]:
    feature_states_by_segment_id = {}  # type: ignore[var-annotated]

    for segment in segments:
        segment_feature_states = feature_states_by_segment_id.setdefault(segment.pk, [])

        for feature_segment in segment.feature_segments.all():
            if feature_segment.environment_id != environment_id:
                continue

            if (
                latest_environment_feature_version_uuids
                and feature_segment.environment_feature_version_id  # type: ignore[operator]
                not in latest_environment_feature_version_uuids
            ):
                continue

            segment_feature_states += _get_prioritised_feature_states(
                feature_segment.feature_states.all()
            )

    return feature_states_by_segment_id
