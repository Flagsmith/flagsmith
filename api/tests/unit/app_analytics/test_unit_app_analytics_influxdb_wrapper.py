from datetime import datetime, timedelta
from typing import Generator, Type
from unittest import mock
from unittest.mock import MagicMock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from django.conf import settings
from django.utils import timezone
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.rest import ApiException
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from urllib3.exceptions import HTTPError

import app_analytics
from app_analytics.influxdb_wrapper import (
    InfluxDBWrapper,
    build_filter_string,
    get_current_api_usage,
    get_event_list_for_organisation,
    get_events_for_organisation,
    get_feature_evaluation_data,
    get_multiple_event_list_for_feature,
    get_multiple_event_list_for_organisation,
    get_range_bucket_mappings,
    get_top_organisations,
    get_usage_data,
)
from organisations.models import Organisation

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
    monkeypatch.setattr(  # type: ignore[attr-defined]
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
    influxdb = InfluxDBWrapper("name")  # type: ignore[no-untyped-call]
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

    influxdb = InfluxDBWrapper("name")  # type: ignore[no-untyped-call]
    influxdb.add_data_point("field_name", "field_value")

    # When
    influxdb.write()

    # Then
    # The write API was called
    mock_write_api.write.assert_called()


def test_influx_db_wrapper_query__http_error__logs_expected(
    mocker: MockerFixture,
) -> None:
    # Given
    expected_exception = HTTPError("HTTP error occurred")
    mock_query_api = mocker.patch(
        "app_analytics.influxdb_wrapper.influxdb_client.query_api",
        autospec=True,
    )
    mock_query_api.return_value.query.side_effect = expected_exception
    capture_exception_mock = mocker.patch(
        "app_analytics.influxdb_wrapper.capture_exception",
        autospec=True,
    )

    influxdb = InfluxDBWrapper("name")  # type: ignore[no-untyped-call]

    # When
    result = influxdb.influx_query_manager()

    # Then
    assert result == []
    capture_exception_mock.assert_called_once_with(expected_exception)


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_influx_db_query_when_get_events_then_query_api_called(monkeypatch):  # type: ignore[no-untyped-def]
    expected_query = (
        (
            f'from(bucket:"{read_bucket}") |> range(start: 2022-12-20T09:09:47.325132+00:00, '
            "stop: 2023-01-19T09:09:47.325132+00:00) "
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


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_influx_db_query_when_get_events_list_then_query_api_called(
    mocker: MockerFixture,
) -> None:
    query = (
        f'from(bucket:"{read_bucket}") '
        f"|> range(start: 2022-12-20T09:09:47.325132+00:00, stop: 2023-01-19T09:09:47.325132+00:00) "
        f'|> filter(fn:(r) => r._measurement == "api_call") '
        f'|> filter(fn: (r) => r["organisation_id"] == "{org_id}") '
        f'|> drop(columns: ["organisation", "organisation_id", "type", "project", '
        f'"project_id", "environment", "environment_id", "host"]) '
        f'|> aggregateWindow(every: 24h, fn: sum, timeSrc: "_start")'
    )
    mock_influxdb_client = mocker.patch(
        "app_analytics.influxdb_wrapper.influxdb_client",
        autospec=True,
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
@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_influx_db_query_when_get_multiple_events_for_organisation_then_query_api_called(
    mocker: MockerFixture,
    project_id: int | None,
    environment_id: int | None,
    expected_filters: list[str],
) -> None:
    expected_query = (
        f'from(bucket:"{read_bucket}") '
        "|> range(start: 2022-12-20T09:09:47.325132+00:00, stop: 2023-01-19T09:09:47.325132+00:00) "
        f"{build_filter_string(expected_filters)} "
        '|> drop(columns: ["organisation", "organisation_id", "type", "project", '
        '"project_id", "environment", "environment_id", "host"]) '
        '|> group(columns: ["client_application_name", "client_application_version"]) '
        '|> aggregateWindow(every: 24h, fn: sum, timeSrc: "_start")'
    )

    mock_influxdb_client = mocker.patch(
        "app_analytics.influxdb_wrapper.influxdb_client",
        autospec=True,
    )

    mock_query_api = mock_influxdb_client.query_api.return_value

    # When
    get_multiple_event_list_for_organisation(
        org_id, project_id=project_id, environment_id=environment_id
    )

    # Then
    mock_query_api.query.assert_called_once()

    assert mock_query_api.query.call_args_list == [
        mocker.call(
            org=influx_org,
            query=expected_query,
        )
    ]


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_influx_db_query_when_get_multiple_events_for_feature_then_query_api_called(  # type: ignore[no-untyped-def]
    monkeypatch,
):
    query = (
        f'from(bucket:"{read_bucket}") '
        "|> range(start: 2022-12-20T09:09:47.325132+00:00, stop: 2023-01-19T09:09:47.325132+00:00) "
        '|> filter(fn:(r) => r._measurement == "feature_evaluation") '
        '|> filter(fn: (r) => r["_field"] == "request_count") '
        f'|> filter(fn: (r) => r["environment_id"] == "{env_id}") '
        f'|> filter(fn: (r) => r["feature_id"] == "{feature_name}") '
        '|> drop(columns: ["organisation", "organisation_id", "type", "project", '
        '"project_id", "environment", "environment_id", "host"]) '
        '|> group(columns: ["client_application_name", "client_application_version"]) '
        '|> aggregateWindow(every: 24h, fn: sum, createEmpty: false, timeSrc: "_start") '
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


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_get_usage_data__calls_expected(mocker: MockerFixture) -> None:
    # Given
    mocked_get_multiple_event_list_for_organisation = mocker.patch(
        "app_analytics.influxdb_wrapper.get_multiple_event_list_for_organisation",
        autospec=True,
    )

    # When
    get_usage_data(org_id)

    # Then
    date_start = datetime.fromisoformat("2022-12-20T09:09:47.325132+00:00")
    date_stop = datetime.fromisoformat("2023-01-19T09:09:47.325132+00:00")
    mocked_get_multiple_event_list_for_organisation.assert_called_once_with(
        organisation_id=org_id,
        environment_id=None,
        project_id=None,
        date_start=date_start,
        date_stop=date_stop,
        labels_filter=None,
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_get_feature_evaluation_data__calls_expected(mocker: MockerFixture) -> None:
    # Given
    mocked_get_multiple_event_list_for_feature = mocker.patch(
        "app_analytics.influxdb_wrapper.get_multiple_event_list_for_feature",
        autospec=True,
    )

    # When
    get_feature_evaluation_data(
        feature_name,
        env_id,
    )

    # Then
    date_start = datetime.fromisoformat("2022-12-20T09:09:47.325132+00:00")
    mocked_get_multiple_event_list_for_feature.assert_called_once_with(
        feature_name=feature_name,
        environment_id=env_id,
        date_start=date_start,
        labels_filter=None,
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_get_event_list_for_organisation_with_date_stop_set_to_now_and_previously(
    mocker: MockerFixture,
    organisation: Organisation,
) -> None:
    # Given

    now = timezone.now()
    one_day_ago = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    date_stop = now

    record_mock1 = mock.MagicMock()
    record_mock1.__getitem__.side_effect = lambda key: {
        "resource": "resource23",
        "_value": 23,
    }.get(key)
    record_mock1.values = {"_time": one_day_ago}

    record_mock2 = mock.MagicMock()
    record_mock2.__getitem__.side_effect = lambda key: {
        "resource": "resource24",
        "_value": 24,
    }.get(key)
    record_mock2.values = {"_time": two_days_ago}

    result = mock.MagicMock()
    result.records = [record_mock1, record_mock2]

    influx_mock = mocker.patch(
        "app_analytics.influxdb_wrapper.InfluxDBWrapper.influx_query_manager"
    )

    influx_mock.return_value = [result]

    # When
    dataset, labels = get_event_list_for_organisation(
        organisation_id=organisation.id,
        date_stop=date_stop,
    )

    # Then
    assert dataset == {"resource23": [23], "resource24": [24]}
    assert labels == ["2023-01-18", "2023-01-17"]


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
@pytest.mark.parametrize("limit", ["10", ""])
def test_get_top_organisations(
    limit: str,
    mocker: MockerFixture,
) -> None:
    # Given
    record_mock1 = mock.MagicMock()
    record_mock1.values = {"organisation": "123-TestOrg"}
    record_mock1.get_value.return_value = 23

    record_mock2 = mock.MagicMock()
    record_mock2.values = {"organisation": "456-TestCorp"}
    record_mock2.get_value.return_value = 43

    result = mock.MagicMock()
    result.records = [record_mock1, record_mock2]

    influx_mock = mocker.patch(
        "app_analytics.influxdb_wrapper.InfluxDBWrapper.influx_query_manager"
    )

    influx_mock.return_value = [result]
    now = timezone.now()
    date_start = now - timedelta(days=30)

    # When
    dataset = get_top_organisations(date_start=date_start, limit=limit)

    # Then
    assert dataset == {123: 23, 456: 43}

    influx_mock.assert_called_once()
    influx_query_call = influx_mock.call_args
    assert influx_query_call.kwargs["bucket"] == "test_bucket_downsampled_1h"
    assert influx_query_call.kwargs["date_start"] == date_start


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_get_top_organisations_value_error(
    mocker: MockerFixture,
) -> None:
    # Given
    record_mock1 = mock.MagicMock()
    record_mock1.values = {"organisation": "BadData-TestOrg"}
    record_mock1.get_value.return_value = 23

    record_mock2 = mock.MagicMock()
    record_mock2.values = {"organisation": "456-TestCorp"}
    record_mock2.get_value.return_value = 43

    result = mock.MagicMock()
    result.records = [record_mock1, record_mock2]

    influx_mock = mocker.patch(
        "app_analytics.influxdb_wrapper.InfluxDBWrapper.influx_query_manager"
    )

    influx_mock.return_value = [result]
    now = timezone.now()
    date_start = now - timedelta(days=30)

    # When
    dataset = get_top_organisations(date_start=date_start)

    # Then
    # The wrongly typed data does not stop the remaining data
    # from being returned.
    assert dataset == {456: 43}


def test_early_return_for_empty_range_for_influx_query_manager() -> None:
    # When
    now = timezone.now()
    results = InfluxDBWrapper.influx_query_manager(
        date_start=now,
        date_stop=now,
    )

    # Then
    assert results == []


def test_get_range_bucket_mappings_when_less_than_10_days(
    settings: SettingsWrapper,
) -> None:
    # Given
    two_days = timezone.now() - timedelta(days=2)

    # When
    result = get_range_bucket_mappings(two_days)

    # Then
    assert result == settings.INFLUXDB_BUCKET + "_downsampled_15m"


def test_get_range_bucket_mappings_when_more_than_10_days(
    settings: SettingsWrapper,
) -> None:
    # Given
    twelve_days = timezone.now() - timedelta(days=12)

    # When
    result = get_range_bucket_mappings(twelve_days)

    # Then
    assert result == settings.INFLUXDB_BUCKET + "_downsampled_1h"


def test_influx_query_manager_when_date_start_is_set_to_none(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_client = mocker.patch("app_analytics.influxdb_wrapper.influxdb_client")

    # When
    InfluxDBWrapper.influx_query_manager()

    # Then
    mock_client.query_api.assert_called_once()


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_get_top_organisation_when_date_start_is_set_to_none(
    mocker: MockerFixture,
) -> None:
    # Given
    influx_mock = mocker.patch(
        "app_analytics.influxdb_wrapper.InfluxDBWrapper.influx_query_manager"
    )
    now = timezone.now()
    date_start = now - timedelta(days=30)

    # When
    get_top_organisations()

    # Then
    influx_query_call = influx_mock.call_args
    assert influx_query_call.kwargs["bucket"] == "test_bucket_downsampled_1h"
    assert influx_query_call.kwargs["date_start"] == date_start


def test_get_current_api_usage(mocker: MockerFixture) -> None:
    # Given
    influx_mock = mocker.patch(
        "app_analytics.influxdb_wrapper.InfluxDBWrapper.influx_query_manager"
    )
    record_mock = mock.MagicMock()
    record_mock.values = {"organisation": "1-TestCorp"}
    record_mock.get_value.return_value = 43

    result = mock.MagicMock()
    result.records = [record_mock]
    influx_mock.return_value = [result]

    # When
    result = get_current_api_usage(
        organisation_id=1,
        date_start=timezone.now() - timedelta(days=30),
    )  # type: ignore[assignment]

    # Then
    assert result == 43
