"""
Integration tests for the flagd diagnostics endpoint
(``/api/v1/flagd/diagnostics.json``). The endpoint surfaces translation
warnings (type mismatches, REGEX skipped, etc.) without serving the
sync document, so operators can audit an environment before it bites a
flagd consumer.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from segments.models import Condition, Segment, SegmentRule


@pytest.mark.django_db
def test_flagd_diagnostics__valid_server_key__returns_report(
    server_side_sdk_client: APIClient,
    environment: int,
) -> None:
    # Given a healthy environment
    url = reverse("api-v1:flagd:diagnostics")

    # When the diagnostics endpoint is called
    response = server_side_sdk_client.get(url)

    # Then the report is returned with summary metadata
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "flagSetId" in body
    assert body["summary"]["totalWarnings"] == 0
    assert body["features"] == []


@pytest.mark.django_db
def test_flagd_diagnostics__missing_key__returns_403(
    api_client: APIClient,
    environment: int,
) -> None:
    # Given no auth header
    url = reverse("api-v1:flagd:diagnostics")

    # When called
    response = api_client.get(url)

    # Then unauthorised
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_flagd_diagnostics__regex_segment__warning_surfaced_per_feature(
    server_side_sdk_client: APIClient,
    environment: int,
    project: int,
    feature: int,
    feature_name: str,
) -> None:
    # Given a segment with a REGEX condition (which flagd can't represent)
    segment = Segment.objects.create(name="Email Domain", project_id=project)
    parent_rule = SegmentRule.objects.create(segment=segment, type="ALL")
    child_rule = SegmentRule.objects.create(rule=parent_rule, type="ALL")
    Condition.objects.create(
        rule=child_rule,
        operator="REGEX",
        property="email",
        value=r".*@example\.com$",
    )

    # When the diagnostics endpoint is called
    url = reverse("api-v1:flagd:diagnostics")
    response = server_side_sdk_client.get(url)

    # Then the report flags warnings (REGEX surfaces as
    # environmentWarnings since segments are environment-wide)
    body = response.json()
    assert body["summary"]["totalWarnings"] >= 1
    all_reasons = {w["reason"] for w in body.get("environmentWarnings", [])} | {
        w["reason"]
        for feature_entry in body["features"]
        for w in feature_entry["warnings"]
    }
    assert "regex_unsupported" in all_reasons
