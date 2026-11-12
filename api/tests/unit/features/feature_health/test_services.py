import uuid
from unittest.mock import MagicMock

from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.models import Environment
from features.feature_health.models import (
    FeatureHealthEvent,
    FeatureHealthEventType,
    FeatureHealthProvider,
)
from features.feature_health.services import (
    create_feature_health_events_from_provider,
    dismiss_feature_health_event,
    get_provider_response,
)
from features.feature_health.types import (
    FeatureHealthEventData,
    FeatureHealthProviderResponse,
)
from features.models import Feature


def test_get_provider_response__invalid_provider__returns_none_and_logs_error(
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
        provider_name="Webhook",
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


def test_create_feature_health_events_from_provider__events_in_several_environments__sends_feature_health_updated_per_environment(
    feature: Feature,
    environment: Environment,
    feature_health_provider: FeatureHealthProvider,
    feature_health_updated_receiver: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "features.feature_health.services.get_provider_response",
        return_value=FeatureHealthProviderResponse(
            events=[
                FeatureHealthEventData(
                    feature_name=feature.name,
                    environment_name=environment.name,
                    type=FeatureHealthEventType.UNHEALTHY,
                    provider_name="Webhook",
                    external_id="alert-1",
                ),
                FeatureHealthEventData(
                    feature_name=feature.name,
                    environment_name=environment.name,
                    type=FeatureHealthEventType.UNHEALTHY,
                    provider_name="Webhook",
                    external_id="alert-2",
                ),
                FeatureHealthEventData(
                    feature_name=feature.name,
                    type=FeatureHealthEventType.UNHEALTHY,
                    provider_name="Webhook",
                ),
            ]
        ),
    )

    # When
    create_feature_health_events_from_provider(feature_health_provider, "payload")

    # Then
    assert feature_health_updated_receiver.call_count == 2
    assert {
        call.kwargs["environment"]
        for call in feature_health_updated_receiver.call_args_list
    } == {environment, None}
    assert all(
        call.kwargs["feature"] == feature
        for call in feature_health_updated_receiver.call_args_list
    )


def test_create_feature_health_events_from_provider__unhealthy_event__sends_feature_health_updated_after_tag_update(
    feature: Feature,
    environment: Environment,
    feature_health_provider: FeatureHealthProvider,
    feature_health_updated_receiver: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "features.feature_health.services.get_provider_response",
        return_value=FeatureHealthProviderResponse(
            events=[
                FeatureHealthEventData(
                    feature_name=feature.name,
                    environment_name=environment.name,
                    type=FeatureHealthEventType.UNHEALTHY,
                    provider_name="Webhook",
                ),
            ]
        ),
    )
    tag_labels_seen_by_receiver: list[list[str]] = []
    feature_health_updated_receiver.side_effect = lambda feature, **kwargs: (
        tag_labels_seen_by_receiver.append(
            list(feature.tags.values_list("label", flat=True))
        )
    )

    # When
    create_feature_health_events_from_provider(feature_health_provider, "payload")

    # Then
    assert tag_labels_seen_by_receiver == [["Unhealthy"]]


def test_create_feature_health_events_from_provider__invalid_payload__does_not_send_feature_health_updated(
    feature_health_provider: FeatureHealthProvider,
    feature_health_updated_receiver: MagicMock,
) -> None:
    # Given
    invalid_payload = "invalid"

    # When
    create_feature_health_events_from_provider(feature_health_provider, invalid_payload)

    # Then
    feature_health_updated_receiver.assert_not_called()


def test_dismiss_feature_health_event__unhealthy_event__sends_feature_health_updated(
    feature: Feature,
    environment: Environment,
    feature_health_updated_receiver: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    unhealthy_event = FeatureHealthEvent.objects.create(
        feature=feature,
        environment=environment,
        provider_name="Webhook",
        external_id="test_external_id",
        type=FeatureHealthEventType.UNHEALTHY,
    )

    # When
    dismiss_feature_health_event(unhealthy_event, mocker.MagicMock())

    # Then
    feature_health_updated_receiver.assert_called_once_with(
        signal=mocker.ANY,
        sender=Feature,
        feature=feature,
        environment=environment,
    )
