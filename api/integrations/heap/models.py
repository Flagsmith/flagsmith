from django.db import models

from environments.models import Environment
from integrations.common.models import IntegrationsModel


class HeapConfiguration(IntegrationsModel):
    environment = models.OneToOneField(
        Environment, related_name="heap_config", on_delete=models.CASCADE
    )

    def natural_key(self):
        return self.environment_id, self.api_key
