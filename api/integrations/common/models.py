import logging

from core.models import SoftDeleteExportableModel
from django.db import models
from django_lifecycle import (
    AFTER_SAVE,
    AFTER_UPDATE,
    LifecycleModelMixin,
    hook,
)

from environments.models import Environment

logger = logging.getLogger(__name__)


class IntegrationsModel(SoftDeleteExportableModel):
    base_url = models.URLField(blank=False, null=True)
    api_key = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        abstract = True


class EnvironmentIntegrationModel(LifecycleModelMixin, IntegrationsModel):
    class Meta:
        abstract = True

    @hook(AFTER_SAVE)
    def write_environment_to_dynamodb(self):
        if not hasattr(self, "environment_id"):
            logger.warning(
                "Failed to write environment to DynamoDB. "
                "Model class '%s' has no environment_id attribute.",
                self.__class__.__name__,
            )
            return
        Environment.write_environments_to_dynamodb(environment_id=self.environment_id)

    @hook(AFTER_UPDATE)
    def clear_environment_cache(self):
        self.environment.clear_environment_cache()
