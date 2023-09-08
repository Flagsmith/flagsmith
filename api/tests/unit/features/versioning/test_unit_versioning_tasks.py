from pytest_mock import MockerFixture

from environments.models import Environment
from features.models import Feature
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import (
    enable_v2_versioning,
    trigger_update_version_webhooks,
)
from webhooks.webhooks import WebhookEventType


def test_enable_v2_versioning(
    environment: Environment, feature: Feature, multivariate_feature: Feature
) -> None:
    # When
    enable_v2_versioning(environment.id)

    # Then
    assert EnvironmentFeatureVersion.objects.filter(
        environment=environment, feature=feature
    ).exists()
    assert EnvironmentFeatureVersion.objects.filter(
        environment=environment, feature=multivariate_feature
    ).exists()

    environment.refresh_from_db()
    assert environment.use_v2_feature_versioning is True


def test_trigger_update_version_webhooks(
    environment_v2_versioning: Environment, feature: Feature, mocker: MockerFixture
) -> None:
    # Given
    version = EnvironmentFeatureVersion.objects.get(
        feature=feature, environment=environment_v2_versioning
    )
    feature_state = version.feature_states.first()

    mock_call_environment_webhooks = mocker.patch(
        "features.versioning.tasks.call_environment_webhooks"
    )

    # When
    trigger_update_version_webhooks(str(version.uuid))

    # Then
    mock_call_environment_webhooks.assert_called_once_with(
        environment=environment_v2_versioning,
        data={
            "uuid": str(version.uuid),
            "feature": {"id": feature.id, "name": feature.name},
            "published_by": None,
            "feature_states": [
                {
                    "enabled": feature_state.enabled,
                    "value": feature_state.get_feature_state_value(),
                }
            ],
        },
        event_type=WebhookEventType.NEW_VERSION_PUBLISHED,
    )
