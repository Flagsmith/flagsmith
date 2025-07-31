import uuid

from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.models import Environment
from features.feature_health.models import FeatureHealthEvent, FeatureHealthEventType
from features.feature_health.services import (
    dismiss_feature_health_event,
    get_provider_response,
)
from features.models import Feature


def test_get_provider_response__invalid_provider__return_none__log_expected(
    mocker: MockerFixture,
    log: "StructuredLogCapture",
) -> None:
    # Given
    expected_provider_name = "invalid_provider"
    expected_provider_uuid = uuid.uuid4()

    invalid_provider_mock = mocker.MagicMock()
    invalid_provider_mock.name = expected_provider_name
    invalid_provider_mock.uuid = expected_provider_uuid

    # When
    response = get_provider_response(invalid_provider_mock, "payload")

    # Then
    assert response is None
    assert log.events == [
        {
            "event": "feature-health-provider-error",
            "level": "error",
            "provider_id": expected_provider_uuid,
            "provider_name": expected_provider_name,
            "exc_info": mocker.ANY,
        },
    ]
    assert isinstance(log.events[0]["exc_info"], KeyError)


def test_dismiss_feature_health_event__healthy_event__log_expected(
    feature: Feature,
    environment: Environment,
    mocker: MockerFixture,
    log: "StructuredLogCapture",
) -> None:
    # Given
    healthy_event = FeatureHealthEvent.objects.create(
        feature=feature,
        environment=environment,
        provider_name="Sample",
        external_id="test_external_id",
        type=FeatureHealthEventType.HEALTHY,
    )

    # When
    dismiss_feature_health_event(healthy_event, mocker.MagicMock())

    # Then
    assert log.events == [
        {
            "event": "feature-health-event-dismissal-not-supported",
            "feature_health_event_external_id": healthy_event.external_id,
            "feature_health_event_id": healthy_event.id,
            "feature_health_event_type": healthy_event.type,
            "level": "warning",
            "provider_name": healthy_event.provider_name,
        },
    ]
