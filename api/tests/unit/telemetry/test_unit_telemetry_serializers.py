from unittest import mock

from django.test import override_settings
from telemetry.serializers import TelemetrySerializer
from tests.unit.telemetry.helpers import get_example_telemetry_data


@override_settings(INFLUXDB_TOKEN="some-token")
@mock.patch("telemetry.serializers.get_ip_address_from_request")
@mock.patch("telemetry.serializers.InfluxDBWrapper")
def test_telemetry_serializer_save(MockInfluxDBWrapper, mock_get_ip_address):
    # Given
    data = get_example_telemetry_data()
    serializer = TelemetrySerializer(data=data, context={"request": mock.MagicMock()})

    mock_wrapper = mock.MagicMock()
    MockInfluxDBWrapper.return_value = mock_wrapper

    ip_address = "127.0.0.1"
    mock_get_ip_address.return_value = ip_address

    # When
    serializer.is_valid()  # must be called to access validated data
    serializer.save()

    # Then
    mock_wrapper.add_data_point.assert_called_once_with(
        "heartbeat", 1, tags={**data, "ip_address": ip_address}
    )
    mock_wrapper.write.assert_called_once()
