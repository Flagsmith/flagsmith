from collections.abc import Iterable
from itertools import chain
from typing import TYPE_CHECKING, Dict, List, Optional

from flag_engine.environments.integrations.models import IntegrationModel
from flag_engine.environments.models import (
    EnvironmentAPIKeyModel,
    EnvironmentModel,
    WebhookModel,
)
from flag_engine.features.models import (
    FeatureModel,
    FeatureSegmentModel,
    FeatureStateModel,
    MultivariateFeatureOptionModel,
    MultivariateFeatureStateValueModel,
)
from flag_engine.identities.models import IdentityModel, TraitModel
from flag_engine.organisations.models import OrganisationModel
from flag_engine.projects.models import ProjectModel
from flag_engine.segments.models import (
    SegmentConditionModel,
    SegmentModel,
    SegmentRuleModel,
)

from environments.constants import IDENTITY_INTEGRATIONS_RELATION_NAMES

if TYPE_CHECKING:  # pragma: no cover
    from environments.identities.models import Identity, Trait
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
    from segments.models import Segment, SegmentRule


__all__ = (
    "map_environment_api_key_to_engine",
    "map_environment_to_engine",
    "map_feature_to_engine",
    "map_identity_to_engine",
    "map_mv_option_to_engine",
    "map_segment_to_engine",
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
        type=segment_rule.type,
        rules=[
            map_segment_rule_to_engine(segment_sub_rule)
            for segment_sub_rule in segment_sub_rules
        ],
        conditions=[
            SegmentConditionModel(
                operator=condition.operator,
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
        enabled=feature_state.enabled,
        django_id=feature_state.pk,
        feature_state_value=feature_state.get_feature_state_value(),
        featurestate_uuid=feature_state.uuid,
        feature_segment=feature_segment_model,
        feature=map_feature_to_engine(feature),
        multivariate_feature_state_values=[
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
    return MultivariateFeatureOptionModel(value=mv_option.value, id=mv_option.id)


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
    project: "Project" = environment.project
    organisation: "Organisation" = project.organisation

    # Read relationships - grab all the data needed from the ORM here.
    project_segments: List["Segment"] = project.segments.all()
    project_segment_rules_by_segment_id: Dict[
        int,
        Iterable["SegmentRule"],
    ] = {segment.pk: segment.rules.all() for segment in project_segments}
    project_segment_feature_states_by_segment_id = _get_segment_feature_states(
        project_segments,
        environment.pk,
    )
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
        identity_features=identity_feature_state_models,
        identity_traits=identity_trait_models,
    )


def _get_prioritised_feature_states(
    feature_states: Iterable["FeatureState"],
) -> List["FeatureState"]:
    prioritised_feature_state_by_feature_id = {}
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
) -> Dict[int, List["FeatureState"]]:
    feature_states_by_segment_id = {}
    for segment in segments:
        segment_feature_states = feature_states_by_segment_id.setdefault(segment.pk, [])
        for feature_segment in segment.feature_segments.all():
            if feature_segment.environment_id != environment_id:
                continue
            segment_feature_states += _get_prioritised_feature_states(
                feature_segment.feature_states.all()
            )
    return feature_states_by_segment_id
