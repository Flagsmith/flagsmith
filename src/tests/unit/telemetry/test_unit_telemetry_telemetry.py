import json
from unittest import mock

import responses
from telemetry.telemetry import SelfHostedTelemetryWrapper
from tests.unit.telemetry.helpers import get_example_telemetry_data


@responses.activate
@mock.patch("telemetry.telemetry.TelemetryData")
def test_self_hosted_telemetry_wrapper_send_heartbeat(MockTelemetryData):
    # Given
    # we mock the response from the API
    responses.add(
        responses.POST,
        SelfHostedTelemetryWrapper.TELEMETRY_API_URI,
        json={},
        status=200,
    )

    # and generate some example data that will be sent by mocking the
    # TelemetryData model
    data = get_example_telemetry_data()
    mock_telemetry_data = mock.MagicMock(**data)
    MockTelemetryData.generate_telemetry_data.return_value = mock_telemetry_data

    # When
    # We send the heartbeat
    SelfHostedTelemetryWrapper().send_heartbeat()

    # Then
    # Then a request is made to the API with the expected data
    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.url == SelfHostedTelemetryWrapper.TELEMETRY_API_URI
    )
    assert responses.calls[0].request.body.decode("utf-8") == json.dumps(data)
