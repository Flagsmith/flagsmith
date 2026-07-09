from integrations.common.services import (
    get_latest_integration_health,
    record_integration_health,
)
from integrations.webhook.models import WebhookConfiguration


def test_get_latest_integration_health__no_record__returns_none(environment) -> None:
    # Given
    webhook_config = WebhookConfiguration.objects.create(
        environment=environment, url="https://webhook.url"
    )

    # When
    result = get_latest_integration_health(webhook_config)

    # Then
    assert result is None


def test_get_latest_integration_health__has_record__returns_health_dict(environment):
    # Given
    webhook_config = WebhookConfiguration.objects.create(
        environment=environment, url="https://webhook.url"
    )
    record_integration_health(webhook_config, 200)

    # When
    result = get_latest_integration_health(webhook_config)

    # Then
    assert result is not None
    assert result["status_code"] == 200
    assert result["is_healthy"] is True
    assert "created_at" in result
    assert result["created_at"] is not None


def test_get_latest_integration_health__multiple_records__returns_latest(
    environment,
):
    # Given
    webhook_config = WebhookConfiguration.objects.create(
        environment=environment, url="https://webhook.url"
    )
    record_integration_health(webhook_config, 500)
    record_integration_health(webhook_config, 200)

    # When
    result = get_latest_integration_health(webhook_config)

    # Then
    assert result["status_code"] == 200
    assert result["is_healthy"] is True


def test_get_latest_integration_health__non_healthy_status(environment):
    # Given
    webhook_config = WebhookConfiguration.objects.create(
        environment=environment, url="https://webhook.url"
    )
    record_integration_health(webhook_config, 500)

    # When
    result = get_latest_integration_health(webhook_config)

    # Then
    assert result["status_code"] == 500
    assert result["is_healthy"] is False
