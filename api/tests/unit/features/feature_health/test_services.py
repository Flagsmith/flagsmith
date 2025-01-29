import uuid

from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from features.feature_health.services import get_provider_response


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
            "event": "invalid-feature-health-provider-requested",
            "level": "error",
            "provider_id": expected_provider_uuid,
            "provider_name": expected_provider_name,
        },
    ]
