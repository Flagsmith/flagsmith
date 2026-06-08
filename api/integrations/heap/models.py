from django.db import models

from environments.models import Environment
from integrations.common.models import EnvironmentIntegrationModel
from integrations.heap.constants import DEFAULT_HEAP_API_URL


class HeapConfiguration(EnvironmentIntegrationModel):
    base_url = models.URLField(default=DEFAULT_HEAP_API_URL)
    environment = models.OneToOneField(
        Environment, related_name="heap_config", on_delete=models.CASCADE
    )
