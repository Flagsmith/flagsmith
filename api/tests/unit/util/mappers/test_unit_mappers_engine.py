from datetime import datetime
from typing import TYPE_CHECKING

import pytest
import pytz
from django.utils import timezone
from pytest_mock import MockerFixture

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from features.models import FeatureSegment, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import enable_v2_versioning
from integrations.common.models import IntegrationsModel
from integrations.dynatrace.models import DynatraceConfiguration
from integrations.mixpanel.models import MixpanelConfiguration
from integrations.segment.models import SegmentConfiguration
from integrations.webhook.models import WebhookConfiguration
from segments.models import Condition, Segment, SegmentRule
from users.models import FFAdminUser
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
from util.engine_models.identities.models import (
    IdentityFeaturesList,
    IdentityModel,
)
from util.engine_models.identities.traits.models import TraitModel
from util.engine_models.organisations.models import OrganisationModel
from util.engine_models.projects.models import ProjectModel
from util.engine_models.segments.models import (
    SegmentConditionModel,
    SegmentModel,
    SegmentRuleModel,
)
from util.mappers import engine

if TYPE_CHECKING:
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
    return feature_state  # type: ignore[no-any-return]


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
    return FeatureState.objects.create(  # type: ignore[no-any-return]
        feature_segment=feature_segment,
        feature=feature,
        environment=environment,
        live_from=later_live_from,
        version=2,
    )


def test_map_segment_rule_to_engine__nested_rule__returns_expected_model(
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


def test_map_integration_to_engine__valid_integration__returns_expected_model() -> None:
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


def test_map_integration_to_engine__none__returns_none() -> None:
    # Given / When
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


def test_map_webhook_config_to_engine__valid_config__returns_expected_model() -> None:
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


def test_map_webhook_config_to_engine__none__returns_none() -> None:
    # Given / When
    result = engine.map_webhook_config_to_engine(None)

    # Then
    assert result is None


def test_map_feature_state_to_engine__standard_feature__returns_expected_model(
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
        multivariate_feature_state_values=[],  # type: ignore[arg-type]
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
            priority=segment_multivariate_feature_state.feature_segment.priority,  # type: ignore[union-attr]
        ),
        featurestate_uuid=segment_multivariate_feature_state.uuid,
        feature_state_value="control",
        multivariate_feature_state_values=[  # type: ignore[arg-type]
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


def test_map_environment_to_engine__multiple_segments_and_versions__returns_expected_model(
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
        multivariate_feature_state_values=[],  # type: ignore[arg-type]
    )
    expected_feature_state_model = FeatureStateModel(
        feature=expected_feature_model,
        enabled=False,
        django_id=feature_state.id,
        featurestate_uuid=feature_state.uuid,
        feature_state_value=None,
        multivariate_feature_state_values=[],  # type: ignore[arg-type]
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
        use_identity_overrides_in_local_eval=environment.use_identity_overrides_in_local_eval,
        hide_sensitive_data=environment.hide_sensitive_data,
        hide_disabled_flags=environment.hide_disabled_flags,
        amplitude_config=None,
        dynatrace_config=None,
        heap_config=None,
        mixpanel_config={  # type: ignore[arg-type]
            "base_url": mixpanel_configuration.base_url,
            "api_key": mixpanel_configuration.api_key,
        },
        rudderstack_config=None,
        segment_config=None,  # note: segment configuration should not appear as it was deleted
        webhook_config={  # type: ignore[arg-type]
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


def test_map_environment_to_engine__feature_specific_segment_not_in_env__excludes_segment(
    environment: Environment,
    feature: "Feature",
    feature_specific_segment: Segment,
) -> None:
    # Given
    # `feature_specific_segment` has no `FeatureSegment` pointing at it
    # in this environment, so it has no evaluation path here.

    # When
    result = engine.map_environment_to_engine(environment)

    # Then
    segment_ids = [s.id for s in result.project.segments]
    assert feature_specific_segment.id not in segment_ids


def test_map_environment_to_engine__feature_specific_segment_in_env__includes_segment(
    environment: Environment,
    feature: "Feature",
    feature_specific_segment: Segment,
) -> None:
    # Given
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=feature_specific_segment,
        environment=environment,
    )
    FeatureState.objects.create(
        feature_segment=feature_segment,
        feature=feature,
        environment=environment,
    )

    # When
    result = engine.map_environment_to_engine(environment)

    # Then
    segment_ids = [s.id for s in result.project.segments]
    assert feature_specific_segment.id in segment_ids


def test_map_environment_to_engine__project_wide_segment_not_in_env__includes_segment(
    environment: Environment,
    segment: Segment,
) -> None:
    # Given
    # `segment` is a project-wide segment (Segment.feature_id IS NULL)
    # with no `FeatureSegment` in this environment. Project-wide segments
    # must remain in the environment document regardless.

    # When
    result = engine.map_environment_to_engine(environment)

    # Then
    segment_ids = [s.id for s in result.project.segments]
    assert segment.id in segment_ids


def test_map_environment_api_key_to_engine__valid_key__returns_expected_model(
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


def test_map_identity_to_engine__identity_with_traits_and_overrides__returns_expected_model(
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
                    multivariate_feature_state_values=[],  # type: ignore[arg-type]
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


def test_map_environment_to_engine__different_versions__returns_latest_live_from_feature_state(  # type: ignore[no-untyped-def]
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


def test_map_environment_to_engine__after_v2_versioning_migration__returns_latest_versions(
    environment: Environment,
    feature: "Feature",
    feature_state: FeatureState,
    segment: Segment,
    segment_featurestate: FeatureState,
) -> None:
    """
    Specific test to reproduce an issue seen after migrating our staging environment to
    v2 versioning.
    """

    # Given
    # Multiple versions (old style versioning) of a given environment feature state and segment override
    # to simulate the fact that we will be left with feature states that do NOT have a feature version
    # (because only the latest versions get migrated to v2 versioning).
    v2_environment_feature_state = feature_state.clone(
        env=environment, live_from=timezone.now(), version=2
    )
    v2_environment_feature_state.enabled = True
    v2_environment_feature_state_value = "v2"
    v2_environment_feature_state.feature_state_value.string_value = (
        v2_environment_feature_state_value
    )
    v2_environment_feature_state.save()
    v2_environment_feature_state.feature_state_value.save()

    v2_segment_override = segment_featurestate.clone(
        env=environment, live_from=timezone.now(), version=2
    )
    v2_segment_override.enabled = True
    v2_segment_override_value = "v2-override"
    v2_segment_override.feature_state_value.string_value = v2_segment_override_value
    v2_segment_override.save()
    v2_segment_override.feature_state_value.save()

    enable_v2_versioning(environment.id)

    # When
    result = engine.map_environment_to_engine(environment)

    # Then
    assert result

    assert len(result.feature_states) == 1
    mapped_environment_feature_state = result.feature_states[0]

    assert mapped_environment_feature_state.django_id == v2_environment_feature_state.id
    assert mapped_environment_feature_state.enabled is True
    assert (
        mapped_environment_feature_state.feature_state_value
        == v2_environment_feature_state_value
    )

    assert len(result.project.segments) == 1
    assert len(result.project.segments[0].feature_states) == 1

    mapped_segment_override = result.project.segments[0].feature_states[0]
    assert mapped_segment_override.django_id == v2_segment_override.id
    assert mapped_segment_override.enabled is True
    assert mapped_segment_override.feature_state_value == v2_segment_override_value


def test_map_environment_to_engine__v2_versioning_segment_override_removed__returns_remaining_override(
    environment_v2_versioning: Environment,
    segment: Segment,
    feature: "Feature",
    staff_user: FFAdminUser,
) -> None:
    # Given
    # Another segment
    another_segment = Segment.objects.create(
        name="another_segment", project=feature.project
    )

    # First, let's create a version that includes 2 segment overrides
    v2 = EnvironmentFeatureVersion.objects.create(
        feature=feature, environment=environment_v2_versioning
    )
    for _segment in [segment, another_segment]:
        FeatureState.objects.create(
            feature=feature,
            environment=environment_v2_versioning,
            environment_feature_version=v2,
            feature_segment=FeatureSegment.objects.create(
                feature=feature,
                segment=_segment,
                environment=environment_v2_versioning,
                environment_feature_version=v2,
            ),
        )
    v2.publish(staff_user)

    # Now, let's create another new version which will keep one of the segment overrides
    # and remove the other.
    v3 = EnvironmentFeatureVersion.objects.create(
        feature=feature, environment=environment_v2_versioning
    )

    v3_segment_override = FeatureState.objects.get(
        feature_segment__segment=segment, environment_feature_version=v3
    )
    FeatureState.objects.filter(
        feature_segment__segment=another_segment, environment_feature_version=v3
    ).delete()

    v3.publish(staff_user)

    # When
    environment_model = engine.map_environment_to_engine(environment_v2_versioning)

    # Then
    assert len(environment_model.project.segments[0].feature_states) == 1
    assert (
        environment_model.project.segments[0].feature_states[0].django_id
        == v3_segment_override.id
    )


def test_map_environment_to_evaluation_context__no_identity__returns_environment_only(
    environment: Environment,
) -> None:
    # Given / When
    result = engine.map_environment_to_evaluation_context(environment=environment)

    # Then
    assert result == {
        "environment": {
            "key": environment.api_key,
            "name": environment.name,
        },
    }


def test_map_environment_to_evaluation_context__with_identity__returns_identity_context(
    environment: Environment,
    identity: Identity,
) -> None:
    # Given / When
    result = engine.map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
    )

    # Then
    assert result == {
        "environment": {
            "key": environment.api_key,
            "name": environment.name,
        },
        "identity": {
            "identifier": identity.identifier,
            "key": identity.get_hash_key(
                environment.use_identity_composite_key_for_hashing
            ),
            "traits": {},
        },
    }


def test_map_environment_to_evaluation_context__with_explicit_traits__returns_given_traits(
    environment: Environment,
    identity: Identity,
    trait: Trait,
) -> None:
    # Given / When
    result = engine.map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
        traits=[trait],
    )

    # Then
    assert result == {
        "environment": {
            "key": environment.api_key,
            "name": environment.name,
        },
        "identity": {
            "identifier": identity.identifier,
            "key": identity.get_hash_key(
                environment.use_identity_composite_key_for_hashing
            ),
            "traits": {trait.trait_key: trait.trait_value},
        },
    }


def test_map_environment_to_evaluation_context__no_explicit_traits__returns_identity_traits(
    environment: Environment,
    identity: Identity,
    trait: Trait,
) -> None:
    # Given / When
    result = engine.map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
    )

    # Then
    assert result == {
        "environment": {
            "key": environment.api_key,
            "name": environment.name,
        },
        "identity": {
            "identifier": identity.identifier,
            "key": identity.get_hash_key(
                environment.use_identity_composite_key_for_hashing
            ),
            "traits": {trait.trait_key: trait.trait_value},
        },
    }


def test_map_environment_to_evaluation_context__with_segments__returns_segment_contexts(
    environment: Environment,
    identity_matching_segment: Segment,
) -> None:
    # Given / When
    result = engine.map_environment_to_evaluation_context(
        environment=environment,
        segments=[identity_matching_segment],
    )

    # Then
    segment_key = str(identity_matching_segment.pk)
    assert result == {
        "environment": {
            "key": environment.api_key,
            "name": environment.name,
        },
        "segments": {
            segment_key: engine.map_segment_to_segment_context(
                identity_matching_segment
            ),
        },
    }


def test_map_segment_to_segment_context__segment_with_rule__returns_expected(
    identity_matching_segment: Segment,
) -> None:
    # Given
    condition = Condition.objects.get(
        rule__segment=identity_matching_segment,
    )

    # When
    result = engine.map_segment_to_segment_context(identity_matching_segment)

    # Then
    assert result == {
        "key": str(identity_matching_segment.pk),
        "name": identity_matching_segment.name,
        "rules": [
            {
                "type": "ALL",
                "conditions": [
                    {
                        "property": condition.property,
                        "operator": condition.operator,
                        "value": condition.value,
                    },
                ],
                "rules": [],
            },
        ],
        "metadata": {"pk": identity_matching_segment.pk},
    }


def test_map_rule_to_segment_rule__with_nested_rule__returns_expected(
    segment_rule: SegmentRule,
    identity_matching_segment: Segment,
) -> None:
    # Given
    matching_rule = SegmentRule.objects.get(segment=identity_matching_segment)
    matching_rule.rules.add(segment_rule)
    condition = Condition.objects.get(rule=matching_rule)

    # When
    result = engine.map_rule_to_segment_rule(matching_rule)

    # Then
    assert result == {
        "type": "ALL",
        "conditions": [
            {
                "property": condition.property,
                "operator": condition.operator,
                "value": condition.value,
            },
        ],
        "rules": [
            {
                "type": "ALL",
                "conditions": [],
                "rules": [],
            },
        ],
    }


def test_map_condition_to_segment_condition__valid_condition__returns_expected(
    identity_matching_segment: Segment,
) -> None:
    # Given
    condition = Condition.objects.get(
        rule__segment=identity_matching_segment,
    )

    # When
    result = engine.map_condition_to_segment_condition(condition)

    # Then
    assert result == {
        "property": condition.property,
        "operator": condition.operator,
        "value": condition.value,
    }
