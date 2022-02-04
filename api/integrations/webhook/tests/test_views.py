import json

from django.urls import reverse
from rest_framework import status

from integrations.webhook.models import WebhookConfiguration

valid_webhook_url = "http://my.webhook.com/webhooks"


def test_should_create_webhook_config_when_post(
    admin_client, organisation, environment
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-webhook-list",
        args=[environment.api_key],
    )

    data = {"url": valid_webhook_url, "secret": "random_secret"}

    # When
    response = admin_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert WebhookConfiguration.objects.filter(environment=environment).count() == 1


def test_should_return_BadRequest_when_duplicate_webhook_config_is_posted(
    admin_client, organisation, environment
):
    # Given
    config = WebhookConfiguration.objects.create(
        url=valid_webhook_url, environment=environment
    )
    url = reverse(
        "api-v1:environments:integrations-webhook-list",
        args=[environment.api_key],
    )
    data = {"url": config.url}

    # When
    response = admin_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert WebhookConfiguration.objects.filter(environment=environment).count() == 1


def test_should_update_configuration_when_put(admin_client, organisation, environment):
    # Given
    config = WebhookConfiguration.objects.create(
        url=valid_webhook_url,
        environment=environment,
    )
    url = reverse(
        "api-v1:environments:integrations-webhook-detail",
        args=[environment.api_key, config.id],
    )
    new_url = "https://www.flagsmith.com/new-webhook"

    # When
    response = admin_client.put(
        url,
        data=json.dumps({"url": new_url}),
        content_type="application/json",
    )
    config.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert config.url == new_url


def test_should_return_webhook_config_list_when_requested(
    admin_client, organisation, environment
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-webhook-list",
        args=[environment.api_key],
    )
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_should_remove_configuration_when_delete(
    admin_client, organisation, environment
):
    # Given
    config = WebhookConfiguration.objects.create(
        url=valid_webhook_url, environment=environment
    )

    # When
    url = reverse(
        "api-v1:environments:integrations-webhook-detail",
        args=[environment.api_key, config.id],
    )
    res = admin_client.delete(url)

    # Then
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not WebhookConfiguration.objects.filter(environment=environment).exists()
