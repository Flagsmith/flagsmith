"""
Admin REST endpoint for the per-project flagd toggle.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from integrations.flagd.models import FlagdProjectConfiguration


def _list_url(project_id: int) -> str:
    return reverse(
        "api-v1:projects:integrations-flagd-list",
        kwargs={"project_pk": project_id},
    )


def _detail_url(project_id: int, config_pk: int) -> str:
    return reverse(
        "api-v1:projects:integrations-flagd-detail",
        kwargs={"project_pk": project_id, "pk": config_pk},
    )


@pytest.mark.django_db
def test_flagd_configuration__post_first_time__creates_with_enabled_value(
    admin_client: APIClient,
    project: int,
) -> None:
    # Given there's no configuration row yet for the project
    FlagdProjectConfiguration.objects.filter(project_id=project).delete()

    # When the admin POSTs to create the configuration
    response = admin_client.post(
        _list_url(project), data={"enabled": True}, format="json"
    )

    # Then a row is created with the requested state
    assert response.status_code == status.HTTP_201_CREATED, response.content
    assert response.json()["enabled"] is True
    assert FlagdProjectConfiguration.objects.filter(
        project_id=project, enabled=True
    ).count() == 1


@pytest.mark.django_db
def test_flagd_configuration__patch_enabled_true__flips_toggle(
    admin_client: APIClient,
    project: int,
) -> None:
    # Given an existing disabled config (created by the autouse fixture
    # then forced to disabled here)
    config, _ = FlagdProjectConfiguration.objects.update_or_create(
        project_id=project, defaults={"enabled": False}
    )

    # When the admin PATCHes enabled=true
    response = admin_client.patch(
        _detail_url(project, config.pk),
        data={"enabled": True},
        format="json",
    )

    # Then the toggle flips and a fresh GET sees it
    assert response.status_code == status.HTTP_200_OK, response.content
    assert response.json()["enabled"] is True
    config.refresh_from_db()
    assert config.enabled is True


@pytest.mark.django_db
def test_flagd_configuration__patch_enabled_false__disables_sync_endpoint(
    admin_client: APIClient,
    server_side_sdk_client: APIClient,
    project: int,
    environment: int,
) -> None:
    # Given the conftest already enabled it; sync currently works
    sync_url = reverse("api-v1:flagd:sync")
    assert server_side_sdk_client.get(sync_url).status_code == status.HTTP_200_OK
    config = FlagdProjectConfiguration.objects.get(project_id=project)

    # When the admin disables it
    response = admin_client.patch(
        _detail_url(project, config.pk),
        data={"enabled": False},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK, response.content

    # Then the sync endpoint immediately starts returning 404
    assert server_side_sdk_client.get(sync_url).status_code == status.HTTP_404_NOT_FOUND


