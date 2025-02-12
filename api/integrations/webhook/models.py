from django.db import models
from django_lifecycle import (
    AFTER_DELETE,
    AFTER_SAVE,
    LifecycleModelMixin,
    hook,
)

from environments.models import Environment
from webhooks.models import AbstractBaseSoftDeleteExportableWebhookModel


class WebhookConfiguration(
    LifecycleModelMixin, AbstractBaseSoftDeleteExportableWebhookModel
):
    environment = models.OneToOneField(
        Environment, related_name="webhook_config", on_delete=models.CASCADE
    )

    @hook(AFTER_SAVE)
    @hook(AFTER_DELETE)
    def write_environment_to_dynamodb(self):
        Environment.write_environments_to_dynamodb(environment_id=self.environment_id)
