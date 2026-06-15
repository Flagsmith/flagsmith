"""
Tests for the per-project opt-in gate on the flagd endpoints.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from integrations.flagd.models import FlagdProjectConfiguration


@pytest.mark.django_db
def test_flagd_sync__integration_disabled__returns_404(
    server_side_sdk_client: APIClient,
    project: int,
    environment: int,
) -> None:
    # Given the integration is explicitly disabled for the project
    FlagdProjectConfiguration.objects.filter(project_id=project).update(enabled=False)

    # When the sync endpoint is called
    response = server_side_sdk_client.get(reverse("api-v1:flagd:sync"))

    # Then it returns 404 — the integration isn't enabled
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_flagd_diagnostics__integration_disabled__returns_404(
    server_side_sdk_client: APIClient,
    project: int,
    environment: int,
) -> None:
    # Given the integration is disabled
    FlagdProjectConfiguration.objects.filter(project_id=project).update(enabled=False)

    # When the diagnostics endpoint is called
    response = server_side_sdk_client.get(reverse("api-v1:flagd:diagnostics"))

    # Then it also returns 404
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_flagd_sync__no_configuration_row__returns_404(
    server_side_sdk_client: APIClient,
    project: int,
    environment: int,
) -> None:
    # Given there's no FlagdProjectConfiguration row at all
    FlagdProjectConfiguration.objects.filter(project_id=project).delete()

    # When the sync endpoint is called
    response = server_side_sdk_client.get(reverse("api-v1:flagd:sync"))

    # Then the default (opt-in == False) yields 404
    assert response.status_code == status.HTTP_404_NOT_FOUND
