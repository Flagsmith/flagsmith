from datetime import datetime, timezone

from requests_mock import Mocker as RequestsMocker

from telemetry.control_plane.client import post_usage_snapshot
from telemetry.dataclasses import ApiCallBreakdown, UsageSnapshot


def test_post_usage_snapshot__base64_signature__sends_url_safe_unpadded_bearer_token(
    requests_mock: RequestsMocker,
) -> None:
    # Given
    requests_mock.post("https://cp.example.com/v1/public/usage", status_code=200)
    snapshot = UsageSnapshot(
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

    # When
    post_usage_snapshot(
        base_url="https://cp.example.com",
        snapshot=snapshot,
        signature_b64="+/8=",
    )

    # Then
    assert requests_mock.last_request
    assert requests_mock.last_request.headers["Authorization"] == "Bearer -_8"
