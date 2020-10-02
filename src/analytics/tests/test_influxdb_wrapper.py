from unittest import mock

import analytics
from analytics.influxdb_wrapper import InfluxDBWrapper
from influxdb_client import InfluxDBClient

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


def test_query(monkeypatch):
    # Given
    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client)
    monkeypatch.setattr(analytics.influxdb_wrapper, "read_bucket", "test_downsampled_15m")

    mock_query_api = mock.MagicMock()
    mock_influxdb_client.query_api.return_value = mock_query_api

    influxdb = InfluxDBWrapper("name", "field_name", "field_value")

    # When
    influxdb.get_events_for_organisation(123)

    # Then
    mock_query_api.query.assert_called()

