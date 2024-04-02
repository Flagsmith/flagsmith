from datetime import datetime
from typing import TYPE_CHECKING

import pytest
import pytz
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
from flag_engine.identities.models import (
    IdentityFeaturesList,
    IdentityModel,
    TraitModel,
)
from flag_engine.organisations.models import OrganisationModel
from flag_engine.projects.models import ProjectModel
from flag_engine.segments.models import (
    SegmentConditionModel,
    SegmentModel,
    SegmentRuleModel,
)
from pytest_mock import MockerFixture

from environments.models import Environment
from features.models import FeatureSegment, FeatureState
from integrations.common.models import IntegrationsModel
from integrations.dynatrace.models import DynatraceConfiguration
from integrations.mixpanel.models import MixpanelConfiguration
from integrations.segment.models import SegmentConfiguration
from integrations.webhook.models import WebhookConfiguration
from segments.models import Segment, SegmentRule
from util.mappers import engine

if TYPE_CHECKING:  # pragma: no cover
    from environments.identities import Identity, Trait
    from environments.models import EnvironmentAPIKey
    from features.models import Feature
    from projects.models import Project


@pytest.fixture()
def segment_multivariate_feature_state(
    project: "Project",
    environment: Environment,
    multivariate_feature: "Feature",
) -> FeatureState:
    segment = Segment.objects.create(
        name="segment",
        project=project,
        feature=multivariate_feature,
    )
    feature_segment = FeatureSegment.objects.create(
        feature=multivariate_feature,
        segment=segment,
        environment=environment,
    )
    feature_state = FeatureState.objects.create(
        feature_segment=feature_segment,
        feature=multivariate_feature,
        environment=environment,
    )
    feature_state.multivariate_feature_state_values.create(
        multivariate_feature_option=multivariate_feature.multivariate_options.first(),
        percentage_allocation=100,
    )
    return feature_state


@pytest.fixture
def versioned_segment_feature_state(
    feature: "Feature",
    feature_segment: FeatureSegment,
    environment: Environment,
    segment_featurestate: FeatureState,
) -> FeatureState:
    earlier_live_from = datetime.fromisoformat("2023-06-10T15:12:18")
    later_live_from = datetime.fromisoformat("2023-06-11T15:12:18")
    segment_featurestate.live_from = earlier_live_from
    segment_featurestate.save()
    return FeatureState.objects.create(
        feature_segment=feature_segment,
        feature=feature,
        environment=environment,
        live_from=later_live_from,
        version=2,
    )


def test_map_segment_rule_to_engine__return_expected(
    segment_rule: SegmentRule,
    identity_matching_segment: "Segment",
) -> None:
    # Given
    matching_rule = SegmentRule.objects.get(segment=identity_matching_segment)
    matching_rule.rules.add(segment_rule)

    # When
    result = engine.map_segment_rule_to_engine(matching_rule)

    # Then
    assert result == SegmentRuleModel(
        type="ALL",
        rules=[
            SegmentRuleModel(
                type="ALL",
                rules=[],
                conditions=[],
            )
        ],
        conditions=[
            SegmentConditionModel(
                operator="EQUAL",
                value="value1",
                property_="key1",
            )
        ],
    )


def test_map_integration_to_engine__return_expected() -> None:
    # Given
    class TestIntegration(IntegrationsModel):
        class Meta:
            app_label = "test"

    base_url = "http://someurl"
    api_key = "test"

    integration = TestIntegration(base_url=base_url, api_key=api_key)
    expected_result = IntegrationModel(base_url=base_url, api_key=api_key)

    # When
    result = engine.map_integration_to_engine(integration)

    # Then
    assert result == expected_result


def test_map_integration_to_engine__none__return_expected() -> None:
    # When
    result = engine.map_integration_to_engine(None)

    # Then
    assert result is None


def test_map_integration_to_engine__dynatrace__return_expected() -> None:
    # Given
    base_url = "http://someurl"
    api_key = "test"
    entity_selector = "*"

    integration = DynatraceConfiguration(
        base_url=base_url,
        api_key=api_key,
        entity_selector=entity_selector,
    )
    expected_result = IntegrationModel(
        base_url=base_url,
        api_key=api_key,
        entity_selector=entity_selector,
    )

    # When
    result = engine.map_integration_to_engine(integration)

    # Then
    assert result == expected_result


def test_map_webhook_config_to_engine__return_expected() -> None:
    # Given
    url = "http://someurl"
    secret = "test"

    webhook_config = WebhookConfiguration(
        url=url,
        secret=secret,
    )
    expected_result = WebhookModel(
        url=url,
        secret=secret,
    )

    # When
    result = engine.map_webhook_config_to_engine(webhook_config)

    # Then
    assert result == expected_result


def test_map_webhook_config_to_engine__none__return_expected() -> None:
    # When
    result = engine.map_webhook_config_to_engine(None)

    # Then
    assert result is None


def test_map_feature_state_to_engine__return_expected(
    feature: "Feature",
    feature_state: FeatureState,
) -> None:
    # Given
    expected_result = FeatureStateModel(
        feature=FeatureModel(
            id=feature.id,
            name="Test Feature1",
            type="STANDARD",
        ),
        enabled=False,
        django_id=feature_state.id,
        feature_segment=None,
        featurestate_uuid=feature_state.uuid,
        feature_state_value=None,
        multivariate_feature_state_values=[],
    )

    # When
    result = engine.map_feature_state_to_engine(
        feature_state,
        mv_fs_values=[],
    )

    # Then
    assert result == expected_result


def test_map_feature_state_to_engine__feature_segment__return_expected(
    segment_multivariate_feature_state: FeatureState,
    multivariate_feature: "Feature",
) -> None:
    # Given
    mv_fs_value = (
        segment_multivariate_feature_state.multivariate_feature_state_values.get()
    )
    expected_result = FeatureStateModel(
        feature=FeatureModel(
            id=multivariate_feature.id,
            name="feature",
            type="MULTIVARIATE",
        ),
        enabled=False,
        django_id=segment_multivariate_feature_state.id,
        feature_segment=FeatureSegmentModel(
            priority=segment_multivariate_feature_state.feature_segment.priority,
        ),
        featurestate_uuid=segment_multivariate_feature_state.uuid,
        feature_state_value="control",
        multivariate_feature_state_values=[
            MultivariateFeatureStateValueModel(
                multivariate_feature_option=MultivariateFeatureOptionModel(
                    value=mv_fs_value.multivariate_feature_option.value,
                    id=mv_fs_value.multivariate_feature_option.id,
                ),
                percentage_allocation=mv_fs_value.percentage_allocation,
                id=mv_fs_value.id,
                mv_fs_value_uuid=mv_fs_value.uuid,
            ),
        ],
    )

    # When
    result = engine.map_feature_state_to_engine(
        segment_multivariate_feature_state,
        mv_fs_values=[mv_fs_value],
    )

    # Then
    assert result == expected_result


def test_map_environment_to_engine__return_expected(
    environment: Environment,
    feature: "Feature",
    feature_state: FeatureState,
    segment: Segment,
    feature_segment: FeatureSegment,
    segment_featurestate: FeatureState,
    versioned_segment_feature_state: FeatureState,
) -> None:
    # Given
    environment_2 = Environment.objects.create(
        name="Test Environment 2",
        project=environment.project,
    )
    not_live_segment_feature_state = FeatureState.objects.create(
        feature_segment=feature_segment,
        feature=feature,
        environment=environment,
        version=None,
    )
    # create a non-live feature state to verify it is NOT added to
    # the environment document
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        version=None,
    )
    different_environment_segment_feature_state = FeatureState.objects.create(
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            segment=segment,
            environment=environment_2,
        ),
        feature=feature,
        environment=environment_2,
    )
    mixpanel_configuration = MixpanelConfiguration.objects.create(
        environment=environment,
        api_key="some-key",
    )
    webhook_configuration = WebhookConfiguration.objects.create(
        environment=environment, url="https://my.webhook.com/webhook"
    )
    deleted_segment_configuration = SegmentConfiguration.objects.create(
        environment=environment,
        api_key="some-key",
    )
    deleted_segment_configuration.delete()

    expected_feature_model = FeatureModel(
        id=feature.id, name="Test Feature1", type="STANDARD"
    )
    expected_segment_feature_state_model = FeatureStateModel(
        feature=expected_feature_model,
        enabled=False,
        django_id=versioned_segment_feature_state.id,
        feature_segment=FeatureSegmentModel(
            priority=feature_segment.priority,
        ),
        featurestate_uuid=versioned_segment_feature_state.uuid,
        feature_state_value=None,
        multivariate_feature_state_values=[],
    )
    expected_feature_state_model = FeatureStateModel(
        feature=expected_feature_model,
        enabled=False,
        django_id=feature_state.id,
        featurestate_uuid=feature_state.uuid,
        feature_state_value=None,
        multivariate_feature_state_values=[],
    )
    expected_project_model = ProjectModel(
        id=environment.project.id,
        name="Test Project",
        organisation=OrganisationModel(
            id=environment.project.organisation.id,
            name="Test Org",
            feature_analytics=False,
            stop_serving_flags=False,
            persist_trait_data=True,
        ),
        hide_disabled_flags=False,
        segments=[
            SegmentModel(
                id=segment.id,
                name=segment.name,
                rules=[],
                feature_states=[expected_segment_feature_state_model],
            ),
        ],
        enable_realtime_updates=False,
        server_key_only_feature_ids=[],
    )

    expected_result = EnvironmentModel(
        id=environment.id,
        api_key=environment.api_key,
        project=expected_project_model,
        feature_states=[expected_feature_state_model],
        name=environment.name,
        allow_client_traits=environment.allow_client_traits,
        updated_at=environment.updated_at,
        use_identity_composite_key_for_hashing=environment.use_identity_composite_key_for_hashing,
        hide_sensitive_data=environment.hide_sensitive_data,
        hide_disabled_flags=environment.hide_disabled_flags,
        amplitude_config=None,
        dynatrace_config=None,
        heap_config=None,
        mixpanel_config={
            "base_url": mixpanel_configuration.base_url,
            "api_key": mixpanel_configuration.api_key,
        },
        rudderstack_config=None,
        segment_config=None,  # note: segment configuration should not appear as it was deleted
        webhook_config={
            "url": webhook_configuration.url,
            "secret": webhook_configuration.secret,
        },
    )

    # When
    result = engine.map_environment_to_engine(environment)
    segment_feature_state_uuids = [
        fs.featurestate_uuid for fs in result.project.segments[0].feature_states
    ]

    # Then
    assert len(result.feature_states) == 1
    assert result.feature_states[0].django_id == feature_state.id

    assert result == expected_result

    assert (
        different_environment_segment_feature_state.uuid
        not in segment_feature_state_uuids
    )
    assert not_live_segment_feature_state.uuid not in segment_feature_state_uuids
    assert segment_featurestate.uuid not in segment_feature_state_uuids


def test_map_environment_api_key_to_engine__return_expected(
    environment: Environment,
    environment_api_key: "EnvironmentAPIKey",
) -> None:
    # Given
    client_api_key = environment.api_key

    # When
    result = engine.map_environment_api_key_to_engine(environment_api_key)

    # Then
    assert result == EnvironmentAPIKeyModel(
        id=environment_api_key.pk,
        key=environment_api_key.key,
        created_at=environment_api_key.created_at,
        name=environment_api_key.name,
        client_api_key=client_api_key,
        expires_at=environment_api_key.expires_at,
        active=environment_api_key.active,
    )


def test_map_identity_to_engine__return_expected(
    environment: Environment,
    identity: "Identity",
    feature: "Feature",
    trait: "Trait",
    identity_featurestate: FeatureState,
    mocker: MockerFixture,
) -> None:
    # Given
    environment_api_key = environment.api_key
    expected_result = IdentityModel.construct(
        identifier=identity.identifier,
        environment_api_key=environment_api_key,
        created_date=identity.created_date,
        identity_features=IdentityFeaturesList(
            [
                FeatureStateModel(
                    feature=FeatureModel(
                        id=feature.pk,
                        name=feature.name,
                        type=feature.type,
                    ),
                    enabled=identity_featurestate.enabled,
                    django_id=identity_featurestate.pk,
                    feature_segment=identity_featurestate.feature_segment,
                    featurestate_uuid=identity_featurestate.uuid,
                    feature_state_value=identity_featurestate.get_feature_state_value(),
                    multivariate_feature_state_values=[],
                )
            ]
        ),
        identity_traits=[
            TraitModel(
                trait_key=trait.trait_key,
                trait_value=trait.trait_value,
            )
        ],
        identity_uuid=mocker.ANY,
        django_id=identity.pk,
        composite_key=identity.composite_key,
    )

    # When
    result = engine.map_identity_to_engine(identity)

    # Then
    assert result == expected_result


def test_map_environment_to_engine__returns_correct_feature_state_for_different_versions(
    feature, environment
):
    # Given
    v1_feature_state = FeatureState.objects.get(
        feature=feature, environment=environment
    )

    # Let's simulate an issue that we saw in production where 2 change requests operated on the same
    # feature. One had a live_from of '2023-03-06 06:00:00.000 +0000' and a version of 16 and the
    # other had a live_from of '2023-03-12 06:00:00.000 +0000' of 15. Based on the logic in
    # FeatureState.__gt__(), I would expect that the feature state with the most recent live from,
    # regardless of the fact that it's a lower version would be returned in the mapper.
    v16_feature_state = FeatureState.objects.create(  # noqa
        feature=feature,
        environment=environment,
        live_from=datetime.fromisoformat("2023-03-06 06:00:00.000").replace(
            tzinfo=pytz.UTC
        ),
        version=16,
    )
    v15_feature_state = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        live_from=datetime.fromisoformat("2023-03-12 06:00:00.000").replace(
            tzinfo=pytz.UTC
        ),
        version=15,
    )

    # we also need to make sure that the live_from value of the v1 feature state is earlier than
    # the 2 we have set up for our simulation above.
    v1_feature_state.live_from = datetime.fromisoformat(
        "2023-03-01 06:00:00.000"
    ).replace(tzinfo=pytz.UTC)
    v1_feature_state.save()

    # When
    result = engine.map_environment_to_engine(environment)

    # Then
    assert len(result.feature_states) == 1
    assert result.feature_states[0].django_id == v15_feature_state.id
