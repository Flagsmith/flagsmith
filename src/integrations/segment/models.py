from django.db import models

from environments.models import Environment
from integrations.common.models import IntegrationsModel


class SegmentConfiguration(IntegrationsModel):
    environment = models.OneToOneField(
        Environment, related_name="segment_config", on_delete=models.CASCADE
    )
