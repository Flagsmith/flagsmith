import json
import uuid

import pytest
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.models import Environment
from features.feature_health.exceptions import (
    FeatureHealthEventsNotCreatedError,
    FeatureHealthWebhookPayloadInvalidError,
)
from features.feature_health.models import (
    FeatureHealthEvent,
    FeatureHealthEventType,
    FeatureHealthProvider,
)
from features.feature_health.providers import grafana, webhook
from features.feature_health.services import (
    create_feature_health_events_from_provider,
    dismiss_feature_health_event,
    get_provider_response,
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


def test_get_provider_response__invalid_webhook_payload__raises_and_logs_warning(
    feature_health_provider: FeatureHealthProvider,
    environment: Environment,
    log: "StructuredLogCapture",
) -> None:
    # Given
    payload = json.dumps(
        {
            "feature": "feature_1",
            "environment": environment.name,
            "status": "unhealthy",
            "reason": "Something is broken",
        }
    )

    # When
    with pytest.raises(FeatureHealthWebhookPayloadInvalidError) as exc_info:
        get_provider_response(feature_health_provider, payload)

    # Then
    assert exc_info.value.detail == {
        "detail": "Invalid feature health webhook payload.",
        "code": "invalid_payload",
        "errors": [
            {
                "loc": "reason",
                "msg": "Input should be an object",
                "type": "dict_type",
            },
        ],
    }
    assert log.events == [
        {
            "event": "webhook_payload.invalid",
            "level": "warning",
            "organisation__id": feature_health_provider.project.organisation_id,
            "project__id": feature_health_provider.project_id,
            "environment__id": environment.id,
            "provider__id": feature_health_provider.uuid,
            "provider__name": "Webhook",
            "errors": "reason: Input should be an object",
        },
    ]


@pytest.mark.parametrize(
    "payload, expected_errors",
    [
        ("invalid", "Invalid JSON: expected value at line 1 column 1"),
        (
            json.dumps({"feature": "feature_1", "environment": "unknown"}),
            "status: Field required",
        ),
    ],
)
def test_get_provider_response__invalid_webhook_payload_without_known_environment__logs_without_environment(
    feature_health_provider: FeatureHealthProvider,
    log: "StructuredLogCapture",
    payload: str,
    expected_errors: str,
) -> None:
    # Given / When
    with pytest.raises(FeatureHealthWebhookPayloadInvalidError):
        get_provider_response(feature_health_provider, payload)

    # Then
    assert log.events == [
        {
            "event": "webhook_payload.invalid",
            "level": "warning",
            "organisation__id": feature_health_provider.project.organisation_id,
            "project__id": feature_health_provider.project_id,
            "provider__id": feature_health_provider.uuid,
            "provider__name": "Webhook",
            "errors": expected_errors,
        },
    ]


def test_create_feature_health_events_from_provider__feature_not_found__raises_and_logs_info(
    feature_health_provider: FeatureHealthProvider,
    environment: Environment,
    log: "StructuredLogCapture",
) -> None:
    # Given
    payload = json.dumps(
        {
            "feature": "non_existent",
            "environment": environment.name,
            "status": "unhealthy",
        }
    )

    # When
    with pytest.raises(FeatureHealthEventsNotCreatedError) as exc_info:
        create_feature_health_events_from_provider(feature_health_provider, payload)

    # Then
    assert exc_info.value.detail == {
        "detail": (
            "No feature health events were created: "
            "feature(s) 'non_existent' not found in the project."
        ),
        "code": "no_events_created",
    }
    assert not FeatureHealthEvent.objects.exists()
    assert log.events == [
        {
            "event": "webhook_payload.no_events_created",
            "level": "info",
            "organisation__id": feature_health_provider.project.organisation_id,
            "project__id": feature_health_provider.project_id,
            "environment__id": environment.id,
            "provider__id": feature_health_provider.uuid,
            "provider__name": "Webhook",
            "feature_names": ["non_existent"],
        },
    ]


def test_create_feature_health_events_from_provider__unknown_provider__raises(
    feature_health_provider: FeatureHealthProvider,
) -> None:
    # Given
    feature_health_provider.name = "unknown"

    # When / Then
    with pytest.raises(FeatureHealthEventsNotCreatedError):
        create_feature_health_events_from_provider(feature_health_provider, "{}")


@pytest.mark.parametrize(
    "payload, expected_environment_names",
    [
        ("invalid", []),
        ("[]", []),
        (json.dumps({"environment": 1}), []),
        (json.dumps({"environment": "production"}), ["production"]),
    ],
)
def test_webhook_map_payload_to_environment_names__various_payloads__returns_expected(
    payload: str,
    expected_environment_names: list[str],
) -> None:
    # Given / When
    environment_names = webhook.map_payload_to_environment_names(payload)

    # Then
    assert environment_names == expected_environment_names


@pytest.mark.parametrize(
    "payload, expected_environment_names",
    [
        ("invalid", []),
        ("[]", []),
        (json.dumps({"alerts": {}}), []),
        (
            json.dumps(
                {
                    "alerts": [
                        "invalid",
                        {"labels": "invalid"},
                        {"labels": {"flagsmith_environment": 1}},
                        {"labels": {"flagsmith_environment": "production"}},
                    ]
                }
            ),
            ["production"],
        ),
    ],
)
def test_grafana_map_payload_to_environment_names__various_payloads__returns_expected(
    payload: str,
    expected_environment_names: list[str],
) -> None:
    # Given / When
    environment_names = grafana.map_payload_to_environment_names(payload)

    # Then
    assert environment_names == expected_environment_names
