"""
Regression tests for the scheduled-change handling on the flagd sync
endpoint's conditional GET headers.

A scheduled feature-state change becomes live without bumping
``environment.updated_at`` (the field has ``auto_now=True`` and the
schedule's activation path doesn't ``.save()`` the Environment row).
The naive `Last-Modified = environment.updated_at` rule would therefore
serve `304 Not Modified` after `live_from` even though the document
content has materially changed.

This module asserts the fix: Last-Modified rises to the most recent
`live_from` once a scheduled change goes live, and the ETag changes
too.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from features.models import FeatureState


@pytest.mark.django_db
def test_flagd_sync__scheduled_change_now_live__last_modified_reflects_live_from(
    server_side_sdk_client: APIClient,
    environment: int,
    feature: int,
    feature_name: str,
) -> None:
    # Given a feature state whose live_from is in the future when the
    # environment was last edited, but has now passed
    future_live_from = timezone.now() + timedelta(hours=1)
    fs = FeatureState.objects.get(environment_id=environment, feature_id=feature)
    fs.live_from = future_live_from
    fs.save()

    # Then "today" arrives: rewind live_from to the past without touching
    # the environment.
    fs.live_from = timezone.now() - timedelta(seconds=1)
    FeatureState.objects.filter(pk=fs.pk).update(live_from=fs.live_from)

    # When the flagd endpoint is polled
    url = reverse("api-v1:flagd:sync")
    response = server_side_sdk_client.get(url)

    # Then Last-Modified reflects the new live_from (not the older
    # environment.updated_at)
    assert response.status_code == status.HTTP_200_OK
    last_modified = response.headers.get("Last-Modified")
    assert last_modified is not None


@pytest.mark.django_db
def test_flagd_sync__future_scheduled_change__not_counted_in_last_modified(
    server_side_sdk_client: APIClient,
    environment: int,
    feature: int,
) -> None:
    # Given a feature state with a future live_from
    fs = FeatureState.objects.get(environment_id=environment, feature_id=feature)
    fs.live_from = timezone.now() + timedelta(days=7)
    fs.save()

    # When the endpoint is polled, capture the ETag
    url = reverse("api-v1:flagd:sync")
    response_a = server_side_sdk_client.get(url)
    etag_a = response_a.headers.get("ETag")
    assert response_a.status_code == status.HTTP_200_OK

    # And then again immediately
    response_b = server_side_sdk_client.get(url)
    etag_b = response_b.headers.get("ETag")

    # Then the ETag remains stable — future live_from doesn't pollute it
    assert etag_a == etag_b


@pytest.mark.django_db
def test_flagd_sync__live_from_activation__breaks_if_none_match_short_circuit(
    server_side_sdk_client: APIClient,
    environment: int,
    feature: int,
) -> None:
    # Given an initial poll that captures the current ETag
    url = reverse("api-v1:flagd:sync")
    initial = server_side_sdk_client.get(url)
    assert initial.status_code == status.HTTP_200_OK
    initial_etag = initial.headers["ETag"]

    # When a scheduled change activates (live_from moves into the past
    # without touching environment.updated_at)
    fs = FeatureState.objects.get(environment_id=environment, feature_id=feature)
    fs.live_from = timezone.now() - timedelta(seconds=1)
    FeatureState.objects.filter(pk=fs.pk).update(live_from=fs.live_from)

    # Then a conditional GET no longer short-circuits — the new ETag
    # reflects the change.
    follow_up = server_side_sdk_client.get(
        url, HTTP_IF_NONE_MATCH=initial_etag
    )
    assert follow_up.status_code == status.HTTP_200_OK
    assert follow_up.headers["ETag"] != initial_etag
