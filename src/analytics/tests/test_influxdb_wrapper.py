from unittest import mock

import analytics
from analytics.influxdb_wrapper import InfluxDBWrapper
from analytics.influxdb_wrapper import get_events_for_organisation


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


def test_influx_db_query_when_get_events_then_query_api_(monkeypatch):
    # Given
    org_id = 123
    read_bucket = "_downsampled_15m"
    query = ' from(bucket:"%s") \
                |> range(start: -30d, stop: now()) \
                |> filter(fn:(r) => r._measurement == "api_call") \
                |> filter(fn: (r) => r["_field"] == "request_count") \
                |> filter(fn: (r) => r["organisation_id"] == "%s") \
                |> drop(columns: ["organisation", "resource",  "project", "project_id"]) \
                |> sum()' % (read_bucket, org_id)

    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client)

    mock_query_api = mock.MagicMock()
    mock_influxdb_client.query_api.return_value = mock_query_api

    # When
    get_events_for_organisation(org_id)

    # Then
    mock_query_api.query.assert_called_once_with(org='', query=query)
