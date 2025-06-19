from unittest import mock

import pytest
from pytest_mock import MockerFixture

from app_analytics.models import Resource
from app_analytics.track import (
    track_feature_evaluation_influxdb,
    track_request_googleanalytics,
    track_request_influxdb,
)
from app_analytics.types import FeatureEvaluationKey


@pytest.mark.parametrize(
    "request_uri, expected_ga_requests",
    (
        ("/api/v1/flags/", 2),
        ("/api/v1/identities/", 2),
        ("/api/v1/traits/", 2),
        ("/api/v1/features/", 1),
        ("/health", 1),
    ),
)
@mock.patch("app_analytics.track.requests")
@mock.patch("app_analytics.track.Environment")
def test_track_request_googleanalytics(  # type: ignore[no-untyped-def]
    MockEnvironment, mock_requests, request_uri, expected_ga_requests
):
    """
    Verify that the correct number of calls are made to GA for the various uris.

    All SDK endpoints should send 2 requests as they send a page view and an event (for managing number of API
    requests made by an organisation). All API requests made to the 'admin' API, for managing flags, etc. should
    only send a page view request.
    """
    # Given
    request = mock.MagicMock()
    request.path = request_uri
    environment_api_key = "test"
    request.headers = {"X-Environment-Key": environment_api_key}

    # When
    track_request_googleanalytics(request)  # type: ignore[no-untyped-call]

    # Then
    assert mock_requests.post.call_count == expected_ga_requests


@pytest.mark.parametrize(
    "expected_resource,expected_influxdb_tag",
    (
        (Resource.FLAGS, "flags"),
        (Resource.IDENTITIES, "identities"),
        (Resource.TRAITS, "traits"),
        (Resource.ENVIRONMENT_DOCUMENT, "environment-document"),
    ),
)
def test_track_request_sends_data_to_influxdb_for_tracked_uris(  # type: ignore[no-untyped-def]
    mocker: MockerFixture,
    expected_resource: Resource,
    expected_influxdb_tag: str,
):
    """
    Verify that the correct number of calls are made to InfluxDB for the various uris.
    """
    # Given
    mock_influxdb = mocker.patch("app_analytics.track.InfluxDBWrapper")
    mock_environment = mocker.MagicMock()

    # When
    track_request_influxdb(
        resource=expected_resource,
        host="testserver",
        environment=mock_environment,
        count=1,
        labels={},
    )

    # Then
    mock_influxdb.return_value.add_data_point.assert_called_once()
    assert (
        mock_influxdb.return_value.add_data_point.call_args_list[0][1]["tags"][
            "resource"
        ]
        == expected_influxdb_tag
    )


def test_track_request_sends_host_data_to_influxdb(
    mocker: MockerFixture,
) -> None:
    """
    Verify that host is part of the data send to influxDB
    """
    # Given
    mock_influxdb = mocker.patch("app_analytics.track.InfluxDBWrapper")
    mock_environment = mocker.MagicMock()

    # When
    track_request_influxdb(
        resource=Resource.FLAGS,
        host="testserver",
        environment=mock_environment,
        count=1,
        labels={},
    )

    # Then
    assert (
        mock_influxdb.return_value.add_data_point.call_args_list[0][1]["tags"]["host"]
        == "testserver"
    )


def test_track_feature_evaluation_influxdb(mocker: MockerFixture) -> None:
    # Given
    influx_db_wrapper_class_mock = mocker.patch("app_analytics.track.InfluxDBWrapper")
    influx_db_wrapper_mock = influx_db_wrapper_class_mock.return_value

    data = [
        (FeatureEvaluationKey("foo", ()), 12),
        (FeatureEvaluationKey("bar", ()), 19),
        (FeatureEvaluationKey("baz", (("client_application_name", "test-app"),)), 44),
    ]
    environment_id = 1

    # When
    track_feature_evaluation_influxdb(
        environment_id=environment_id, feature_evaluations=data
    )

    # Then
    assert influx_db_wrapper_mock.add_data_point.call_args_list == [
        mocker.call(
            "request_count",
            12,
            tags={
                "environment_id": environment_id,
                "feature_id": "foo",
            },
        ),
        mocker.call(
            "request_count",
            19,
            tags={
                "environment_id": environment_id,
                "feature_id": "bar",
            },
        ),
        mocker.call(
            "request_count",
            44,
            tags={
                "environment_id": environment_id,
                "feature_id": "baz",
                "client_application_name": "test-app",
            },
        ),
    ]
    influx_db_wrapper_mock.write.assert_called_once()
