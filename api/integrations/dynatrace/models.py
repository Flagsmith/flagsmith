import logging

from django.db import models

from environments.models import Environment
from integrations.common.models import IntegrationsModel

logger = logging.getLogger(__name__)


class DynatraceConfiguration(IntegrationsModel):
    environment = models.OneToOneField(
        Environment, related_name="dynatrace_config", on_delete=models.CASCADE
    )
    entity_selector = models.CharField(max_length=1000, blank=False, null=False)
