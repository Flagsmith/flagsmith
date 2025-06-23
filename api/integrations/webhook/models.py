from django.db import models
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_DELETE,
    AFTER_SAVE,
    LifecycleModelMixin,
    hook,
)

from environments.models import Environment
from webhooks.models import AbstractBaseSoftDeleteExportableWebhookModel


class WebhookConfiguration(
    LifecycleModelMixin,  # type: ignore[misc]
    AbstractBaseSoftDeleteExportableWebhookModel,
):
    environment = models.OneToOneField(
        Environment, related_name="webhook_config", on_delete=models.CASCADE
    )

    @hook(AFTER_SAVE)
    @hook(AFTER_DELETE)
    def write_environment_to_dynamodb(self):  # type: ignore[no-untyped-def]
        Environment.write_environment_documents(environment_id=self.environment_id)
