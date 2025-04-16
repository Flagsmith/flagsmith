from unittest import mock

import pytest
from pytest_mock import MockerFixture

from app_analytics.models import Resource
from app_analytics.track import (
    track_feature_evaluation_influxdb,
    track_request_googleanalytics,
    track_request_influxdb,
)


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
    "expected_resource",
    (
        "flags",
        "identities",
        "traits",
        "environment-document",
    ),
)
def test_track_request_sends_data_to_influxdb_for_tracked_uris(  # type: ignore[no-untyped-def]
    mocker: MockerFixture,
    expected_resource: str,
):
    """
    Verify that the correct number of calls are made to InfluxDB for the various uris.
    """
    # Given
    mock_influxdb = mocker.patch("app_analytics.track.InfluxDBWrapper")
    mock_environment = mocker.MagicMock()

    # When
    track_request_influxdb(
        resource=Resource.get_from_name(expected_resource),
        host="testserver",
        environment=mock_environment,
    )

    # Then
    mock_influxdb.return_value.add_data_point.assert_called_once()
    assert (
        mock_influxdb.return_value.add_data_point.call_args_list[0][1]["tags"][
            "resource"
        ]
        == expected_resource
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
    )

    # Then
    assert (
        mock_influxdb.return_value.add_data_point.call_args_list[0][1]["tags"]["host"]
        == "testserver"
    )


def test_track_feature_evaluation_influxdb(mocker: MockerFixture) -> None:
    # Given
    mock_influxdb_wrapper = mock.MagicMock()
    mocker.patch(
        "app_analytics.track.InfluxDBWrapper", return_value=mock_influxdb_wrapper
    )

    data = {
        "foo": 12,
        "bar": 19,
        "baz": 44,
    }
    environment_id = 1

    # When
    track_feature_evaluation_influxdb(
        environment_id=environment_id, feature_evaluations=data
    )

    # Then
    calls = mock_influxdb_wrapper.add_data_point.call_args_list
    assert len(calls) == 3
    for i, feature_name in enumerate(data):
        assert calls[i].args[0] == "request_count"
        assert calls[i].args[1] == data[feature_name]
        assert calls[i].kwargs["tags"] == {
            "environment_id": environment_id,
            "feature_id": feature_name,
        }

    mock_influxdb_wrapper.write.assert_called_once_with()
