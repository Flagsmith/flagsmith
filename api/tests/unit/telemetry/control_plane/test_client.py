from datetime import datetime, timezone

import pytest
import requests
from pytest_structlog import StructuredLogCapture
from requests_mock import Mocker as RequestsMocker

from telemetry.control_plane.client import post_usage_snapshot
from telemetry.dataclasses import ApiCallBreakdown, UsageSnapshot

USAGE_URL = "https://cp.example.com/v1/public/usage"


@pytest.fixture()
def snapshot() -> UsageSnapshot:
    return UsageSnapshot(
        timestamp=datetime(2026, 1, 14, tzinfo=timezone.utc),
        seat_count=1,
        api_call_total=0,
        api_call_breakdown=ApiCallBreakdown(
            flags=0, identities=0, traits=0, environment_documents=0
        ),
        project_count=0,
        instance_version="1.2.3",
        project_usage=[],
    )


def test_post_usage_snapshot__base64_signature__sends_url_safe_unpadded_bearer_token(
    requests_mock: RequestsMocker,
    snapshot: UsageSnapshot,
) -> None:
    # Given
    requests_mock.post(USAGE_URL, status_code=200)

    # When
    post_usage_snapshot(
        base_url="https://cp.example.com",
        snapshot=snapshot,
        signature_b64="+/8=",
    )

    # Then
    assert requests_mock.last_request
    assert requests_mock.last_request.headers["Authorization"] == "Bearer -_8"


def test_post_usage_snapshot__accepted__logs_pushed(
    requests_mock: RequestsMocker,
    log: StructuredLogCapture,
    snapshot: UsageSnapshot,
) -> None:
    # Given
    requests_mock.post(USAGE_URL, status_code=200)

    # When
    post_usage_snapshot(
        base_url="https://cp.example.com",
        snapshot=snapshot,
        signature_b64="+/8=",
    )

    # Then
    assert log.events == [
        {"event": "snapshot.pushed", "level": "info", "status_code": 200}
    ]


def test_post_usage_snapshot__rejected__raises_http_error(
    requests_mock: RequestsMocker,
    log: StructuredLogCapture,
    snapshot: UsageSnapshot,
) -> None:
    # Given
    requests_mock.post(USAGE_URL, status_code=503)

    # When
    with pytest.raises(requests.HTTPError):
        post_usage_snapshot(
            base_url="https://cp.example.com",
            snapshot=snapshot,
            signature_b64="+/8=",
        )

    # Then
    assert log.events == []
