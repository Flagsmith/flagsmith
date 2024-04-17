from datetime import date
from typing import Generator, Type
from unittest import mock
from unittest.mock import MagicMock

import app_analytics
import pytest
from _pytest.monkeypatch import MonkeyPatch
from app_analytics.influxdb_wrapper import (
    InfluxDBWrapper,
    build_filter_string,
    get_event_list_for_organisation,
    get_events_for_organisation,
    get_feature_evaluation_data,
    get_multiple_event_list_for_feature,
    get_multiple_event_list_for_organisation,
    get_usage_data,
)
from django.conf import settings
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.rest import ApiException
from urllib3.exceptions import HTTPError

# Given
org_id = 123
env_id = 1234
feature_id = 12345
feature_name = "test_feature"
influx_org = settings.INFLUXDB_ORG
read_bucket = settings.INFLUXDB_BUCKET + "_downsampled_15m"


@pytest.fixture()
def mock_influxdb_client(monkeypatch: Generator[MonkeyPatch, None, None]) -> MagicMock:
    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(
        app_analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client
    )
    return mock_influxdb_client


@pytest.fixture()
def mock_write_api(mock_influxdb_client: MagicMock) -> MagicMock:
    mock_write_api = mock.MagicMock()
    mock_influxdb_client.write_api.return_value = mock_write_api
    return mock_write_api


def test_write(mock_write_api: MagicMock) -> None:
    # Given
    influxdb = InfluxDBWrapper("name")
    influxdb.add_data_point("field_name", "field_value")

    # When
    influxdb.write()

    # Then
    mock_write_api.write.assert_called()


@pytest.mark.parametrize("exception_class", [HTTPError, InfluxDBError, ApiException])
def test_write_handles_errors(
    mock_write_api: MagicMock,
    exception_class: Type[Exception],
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given
    mock_write_api.write.side_effect = exception_class

    influxdb = InfluxDBWrapper("name")
    influxdb.add_data_point("field_name", "field_value")

    # When
    influxdb.write()

    # Then
    # The write API was called
    mock_write_api.write.assert_called()
    # but the exception was not raised


def test_influx_db_query_when_get_events_then_query_api_called(monkeypatch):
    expected_query = (
        (
            f'from(bucket:"{read_bucket}") |> range(start: -30d, stop: now()) '
            f'|> filter(fn:(r) => r._measurement == "api_call")         '
            f'|> filter(fn: (r) => r["_field"] == "request_count")         '
            f'|> filter(fn: (r) => r["organisation_id"] == "{org_id}") '
            f'|> drop(columns: ["organisation", "project", "project_id", "environment", '
            f'"environment_id"])'
            f"|> sum()"
        )
        .replace(" ", "")
        .replace("\n", "")
    )
    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(
        app_analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client
    )

    mock_query_api = mock.MagicMock()
    mock_influxdb_client.query_api.return_value = mock_query_api

    # When
    get_events_for_organisation(org_id)

    # Then
    mock_query_api.query.assert_called_once()

    call = mock_query_api.query.mock_calls[0]
    assert call[2]["org"] == influx_org
    assert call[2]["query"].replace(" ", "").replace("\n", "") == expected_query


def test_influx_db_query_when_get_events_list_then_query_api_called(monkeypatch):
    query = (
        f'from(bucket:"{read_bucket}") '
        f"|> range(start: -30d, stop: now()) "
        f'|> filter(fn:(r) => r._measurement == "api_call")                   '
        f'|> filter(fn: (r) => r["organisation_id"] == "{org_id}") '
        f'|> drop(columns: ["organisation", "organisation_id", "type", "project", '
        f'"project_id", "environment", "environment_id", "host"])'
        f"|> aggregateWindow(every: 24h, fn: sum)"
    )
    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(
        app_analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client
    )

    mock_query_api = mock.MagicMock()
    mock_influxdb_client.query_api.return_value = mock_query_api

    # When
    get_event_list_for_organisation(org_id)

    # Then
    mock_query_api.query.assert_called_once_with(org=influx_org, query=query)


@pytest.mark.parametrize(
    "project_id, environment_id, expected_filters",
    (
        (
            None,
            None,
            ['r._measurement == "api_call"', f'r["organisation_id"] == "{org_id}"'],
        ),
        (
            1,
            None,
            [
                'r._measurement == "api_call"',
                f'r["organisation_id"] == "{org_id}"',
                'r["project_id"] == "1"',
            ],
        ),
        (
            None,
            1,
            [
                'r._measurement == "api_call"',
                f'r["organisation_id"] == "{org_id}"',
                'r["environment_id"] == "1"',
            ],
        ),
        (
            1,
            1,
            [
                'r._measurement == "api_call"',
                f'r["organisation_id"] == "{org_id}"',
                'r["project_id"] == "1"',
                'r["environment_id"] == "1"',
            ],
        ),
    ),
)
def test_influx_db_query_when_get_multiple_events_for_organisation_then_query_api_called(
    monkeypatch, project_id, environment_id, expected_filters
):
    expected_query = (
        (
            f'from(bucket:"{read_bucket}") '
            "|> range(start: -30d, stop: now()) "
            f"{build_filter_string(expected_filters)}"
            '|> drop(columns: ["organisation", "organisation_id", "type", "project", '
            '"project_id", "environment", "environment_id", "host"]) '
            "|> aggregateWindow(every: 24h, fn: sum)"
        )
        .replace(" ", "")
        .replace("\n", "")
    )
    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(
        app_analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client
    )

    mock_query_api = mock.MagicMock()
    mock_influxdb_client.query_api.return_value = mock_query_api

    # When
    get_multiple_event_list_for_organisation(
        org_id, project_id=project_id, environment_id=environment_id
    )

    # Then
    mock_query_api.query.assert_called_once()

    call = mock_query_api.query.mock_calls[0]
    assert call[2]["org"] == influx_org
    assert call[2]["query"].replace(" ", "").replace("\n", "") == expected_query


def test_influx_db_query_when_get_multiple_events_for_feature_then_query_api_called(
    monkeypatch,
):
    query = (
        f'from(bucket:"{read_bucket}") '
        "|> range(start: -30d, stop: now()) "
        '|> filter(fn:(r) => r._measurement == "feature_evaluation")                   '
        '|> filter(fn: (r) => r["_field"] == "request_count")                   '
        f'|> filter(fn: (r) => r["environment_id"] == "{env_id}")                   '
        f'|> filter(fn: (r) => r["feature_id"] == "{feature_name}") '
        '|> drop(columns: ["organisation", "organisation_id", "type", "project", '
        '"project_id", "environment", "environment_id", "host"])'
        "|> aggregateWindow(every: 24h, fn: sum, createEmpty: false)                    "
        '|> yield(name: "sum")'
    )

    mock_influxdb_client = mock.MagicMock()
    monkeypatch.setattr(
        app_analytics.influxdb_wrapper, "influxdb_client", mock_influxdb_client
    )

    mock_query_api = mock.MagicMock()
    mock_influxdb_client.query_api.return_value = mock_query_api

    # When
    assert get_multiple_event_list_for_feature(env_id, feature_name) == []

    # Then
    mock_query_api.query.assert_called_once_with(org=influx_org, query=query)


def test_get_usage_data(mocker):
    # Given
    influx_data = [
        {
            "Environment-document": None,
            "name": "2023-02-02",
            "Flags": 200,
            "Identities": 300,
            "Traits": 400,
        },
        {
            "Environment-document": 10,
            "name": "2023-02-03",
            "Flags": 10,
            "Identities": 20,
            "Traits": 30,
        },
    ]
    mocked_get_multiple_event_list_for_organisation = mocker.patch(
        "app_analytics.influxdb_wrapper.get_multiple_event_list_for_organisation",
        autospec=True,
        return_value=influx_data,
    )

    # When
    usage_data = get_usage_data(org_id)

    # Then
    mocked_get_multiple_event_list_for_organisation.assert_called_once_with(
        org_id, None, None
    )

    assert len(usage_data) == 2

    assert usage_data[0].day == date(year=2023, month=2, day=2)
    assert usage_data[0].flags == 200
    assert usage_data[0].identities == 300
    assert usage_data[0].traits == 400
    assert usage_data[0].environment_document is None

    assert usage_data[1].day == date(year=2023, month=2, day=3)
    assert usage_data[1].flags == 10
    assert usage_data[1].identities == 20
    assert usage_data[1].traits == 30
    assert usage_data[1].environment_document == 10


def test_get_feature_evaluation_data(mocker):
    # Given
    influx_data = [
        {"some-feature": 100, "datetime": "2023-01-08"},
        {"some-feature": 200, "datetime": "2023-01-09"},
    ]
    mocked_get_multiple_event_list_for_feature = mocker.patch(
        "app_analytics.influxdb_wrapper.get_multiple_event_list_for_feature",
        autospec=True,
        return_value=influx_data,
    )

    # When
    feature_evaluation_data = get_feature_evaluation_data(
        feature_name,
        env_id,
    )

    # Then
    mocked_get_multiple_event_list_for_feature.assert_called_once_with(
        feature_name=feature_name, environment_id=env_id, period="30d"
    )

    assert len(feature_evaluation_data) == 2

    assert feature_evaluation_data[0].day == date(year=2023, month=1, day=8)
    assert feature_evaluation_data[0].count == 100

    assert feature_evaluation_data[1].day == date(year=2023, month=1, day=9)
    assert feature_evaluation_data[1].count == 200
