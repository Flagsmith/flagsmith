import pytest

from integrations.webhook.models import WebhookConfiguration


@pytest.fixture()
def integration_webhook_config(environment):
    return WebhookConfiguration.objects.create(
        url="https://flagsmit.com/test-webhook",
        environment=environment,
    )
