from unittest import mock

import analytics
from analytics.influxdb_wrapper import InfluxDBWrapper


def test_write(monkeypatch):
    # Given
    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client)

    mock_write_api = mock.MagicMock()
    mock_influxdb_client.write_api.return_value = mock_write_api

    influxdb = InfluxDBWrapper("name", "field_name", "field_value")

    # When
    influxdb.write()

    # Then
    mock_write_api.write.assert_called()
