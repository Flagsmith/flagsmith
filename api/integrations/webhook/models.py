from django.db import models

from environments.models import Environment
from webhooks.models import AbstractBaseWebhookModel


class WebhookConfiguration(AbstractBaseWebhookModel):
    environment = models.OneToOneField(
        Environment, related_name="webhook_config", on_delete=models.CASCADE
    )
