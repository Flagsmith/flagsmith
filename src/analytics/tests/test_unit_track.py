from unittest import mock

import pytest

from analytics.track import track_request_googleanalytics, track_request_influxdb


@pytest.mark.parametrize("request_uri, expected_ga_requests", (
        ("/api/v1/flags/", 2),
        ("/api/v1/identities/", 2),
        ("/api/v1/traits/", 2),
        ("/api/v1/features/", 1),
        ("/health", 1)
))
@mock.patch("analytics.track.requests")
@mock.patch("analytics.track.Environment")
def test_track_request_googleanalytics(MockEnvironment, mock_requests, request_uri, expected_ga_requests):
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
    track_request_googleanalytics(request)

    # Then
    assert mock_requests.post.call_count == expected_ga_requests


@pytest.mark.parametrize("request_uri", (
        ("/api/v1/flags/"),
        ("/api/v1/identities/"),
        ("/api/v1/traits/"),
        ("/api/v1/features/"),
        ("/health")
))
@mock.patch("analytics.track.requests")
@mock.patch("analytics.track.Environment")
def test_track_request_influxdb(MockEnvironment, mock_requests, request_uri):
    """
    Verify that the correct number of calls are made to InfluxDB for the various uris.
    """
    # Given
    request = mock.MagicMock()
    request.path = request_uri
    environment_api_key = "test"
    request.headers = {"X-Environment-Key": environment_api_key}

    # When
    track_request_influxdb(request)
