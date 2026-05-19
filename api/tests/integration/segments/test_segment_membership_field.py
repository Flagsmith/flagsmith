from datetime import datetime, timezone
from typing import Any

from rest_framework import status
from rest_framework.test import APIClient

from segment_membership.models import SegmentMembershipCount


def test_get_segment__no_memberships__returns_empty_list(
    admin_client: APIClient,
    project: int,
    segment: int,
) -> None:
    # Given a segment with no materialised SegmentMembershipCount rows
    # When the segment is fetched
    response = admin_client.get(f"/api/v1/projects/{project}/segments/{segment}/")

    # Then the membership_counts field is present and empty
    assert response.status_code == status.HTTP_200_OK
    body: dict[str, Any] = response.json()
    assert body["membership_counts"] == []


def test_get_segment__one_membership_per_environment__returns_per_env_counts(
    admin_client: APIClient,
    project: int,
    segment: int,
    environment: int,
) -> None:
    # Given one SegmentMembershipCount row in this segment's environment
    synced_at = datetime(2026, 5, 1, tzinfo=timezone.utc)
    SegmentMembershipCount.objects.create(
        segment_id=segment,
        environment_id=environment,
        count=42,
        last_synced_at=synced_at,
    )

    # When the segment is fetched
    response = admin_client.get(f"/api/v1/projects/{project}/segments/{segment}/")

    # Then the membership_counts field carries one entry keyed by environment id
    assert response.status_code == status.HTTP_200_OK
    body: dict[str, Any] = response.json()
    assert body["membership_counts"] == [
        {
            "environment": environment,
            "count": 42,
            "last_synced_at": synced_at.isoformat().replace("+00:00", "Z"),
        }
    ]
