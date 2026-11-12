from django.db import models

from environments.models import Environment
from integrations.common.models import EnvironmentIntegrationModel


class SegmentConfiguration(EnvironmentIntegrationModel):
    environment = models.OneToOneField(
        Environment, related_name="segment_config", on_delete=models.CASCADE
    )
