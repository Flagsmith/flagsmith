import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from integrations.discord.models import DiscordConfiguration
from projects.models import Project

WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc-DEF_1"


def test_discord_view__create_configuration__persists_webhook(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    url = reverse("api-v1:projects:integrations-discord-list", args=[project.id])

    # When
    response = admin_client_new.post(
        url, data=json.dumps({"base_url": WEBHOOK_URL}), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    config = DiscordConfiguration.objects.get(project=project)
    assert config.base_url == WEBHOOK_URL
    assert response.json()["base_url"] == WEBHOOK_URL


@pytest.mark.parametrize(
    "base_url",
    [
        "https://example.com/api/webhooks/123/abc",
        "http://discord.com/api/webhooks/123/abc",
        "https://discord.com/api/webhooks/not-a-number/abc",
        "https://discord.com.evil.com/api/webhooks/123/abc",
    ],
)
def test_discord_view__create_configuration_not_a_discord_webhook__returns_400(
    admin_client_new: APIClient,
    project: Project,
    base_url: str,
) -> None:
    # Given
    url = reverse("api-v1:projects:integrations-discord-list", args=[project.id])

    # When
    response = admin_client_new.post(
        url, data=json.dumps({"base_url": base_url}), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "base_url" in response.json()
    assert not DiscordConfiguration.objects.filter(project=project).exists()


def test_discord_view__create_configuration_twice__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    DiscordConfiguration.objects.create(project=project, base_url=WEBHOOK_URL)
    url = reverse("api-v1:projects:integrations-discord-list", args=[project.id])

    # When
    response = admin_client_new.post(
        url, data=json.dumps({"base_url": WEBHOOK_URL}), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_discord_view__delete_then_recreate__restores_soft_deleted_configuration(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    config = DiscordConfiguration.objects.create(project=project, base_url=WEBHOOK_URL)
    list_url = reverse("api-v1:projects:integrations-discord-list", args=[project.id])
    detail_url = reverse(
        "api-v1:projects:integrations-discord-detail", args=[project.id, config.id]
    )

    # When
    deleted = admin_client_new.delete(detail_url)
    recreated = admin_client_new.post(
        list_url,
        data=json.dumps({"base_url": WEBHOOK_URL.replace("123", "456")}),
        content_type="application/json",
    )

    # Then
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    assert recreated.status_code == status.HTTP_201_CREATED
    assert recreated.json()["id"] == config.id
    config.refresh_from_db()
    assert config.base_url.startswith("https://discord.com/api/webhooks/456/")


def test_discord_view__create_configuration_url_too_long__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given: a well-formed Discord webhook URL longer than the 200-character column
    base_url = f"https://discord.com/api/webhooks/123/{'a' * 200}"
    url = reverse("api-v1:projects:integrations-discord-list", args=[project.id])

    # When
    response = admin_client_new.post(
        url, data=json.dumps({"base_url": base_url}), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "base_url" in response.json()
    assert not DiscordConfiguration.objects.filter(project=project).exists()
