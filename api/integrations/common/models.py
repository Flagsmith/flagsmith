import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_SAVE,
    AFTER_UPDATE,
    LifecycleModelMixin,
    hook,
)

from core.models import SoftDeleteExportableModel
from environments.models import Environment

logger = logging.getLogger(__name__)


class IntegrationsModel(SoftDeleteExportableModel):
    base_url = models.URLField(blank=False, null=True)
    api_key = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        abstract = True


class EnvironmentIntegrationModel(LifecycleModelMixin, IntegrationsModel):  # type: ignore[misc]
    class Meta:
        abstract = True

    @hook(AFTER_SAVE)
    def write_environment_to_dynamodb(self):  # type: ignore[no-untyped-def]
        if not hasattr(self, "environment_id"):
            logger.warning(
                "Failed to write environment to DynamoDB. "
                "Model class '%s' has no environment_id attribute.",
                self.__class__.__name__,
            )
            return
        Environment.write_environment_documents(environment_id=self.environment_id)

    @hook(AFTER_UPDATE)
    def clear_environment_cache(self):  # type: ignore[no-untyped-def]
        self.environment.clear_environment_cache()


class IntegrationHealthRecord(models.Model):
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    status_code = models.PositiveIntegerField()
