from django.db import models

from environments.models import Environment
from integrations.common.models import EnvironmentIntegrationModel


class HeapConfiguration(EnvironmentIntegrationModel):
    environment = models.OneToOneField(
        Environment, related_name="heap_config", on_delete=models.CASCADE
    )
