from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from environments.models import Environment
from features.feature_health.tasks import update_feature_unhealthy_tag
from features.models import Feature


def test_update_feature_unhealthy_tag__no_environment_ids__sends_feature_health_updated_without_environment(
    feature: Feature,
    feature_health_updated_receiver: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given / When
    update_feature_unhealthy_tag(feature.id)

    # Then
    feature_health_updated_receiver.assert_called_once_with(
        signal=mocker.ANY,
        sender=Feature,
        feature=feature,
        environment=None,
    )


def test_update_feature_unhealthy_tag__deleted_environment__does_not_send_feature_health_updated_for_it(
    feature: Feature,
    environment: Environment,
    feature_health_updated_receiver: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    deleted_environment_id = environment.id + 1000

    # When
    update_feature_unhealthy_tag(
        feature.id,
        environment_ids=[environment.id, deleted_environment_id],
    )

    # Then
    feature_health_updated_receiver.assert_called_once_with(
        signal=mocker.ANY,
        sender=Feature,
        feature=feature,
        environment=environment,
    )


def test_update_feature_unhealthy_tag__deleted_feature__does_not_send_feature_health_updated(
    feature: Feature,
    environment: Environment,
    feature_health_updated_receiver: MagicMock,
) -> None:
    # Given
    feature_id = feature.id
    feature.delete()

    # When
    update_feature_unhealthy_tag(feature_id, environment_ids=[environment.id])

    # Then
    feature_health_updated_receiver.assert_not_called()
