from django.db import models

from environments.models import Environment
from integrations.common.models import EnvironmentIntegrationModel


class RudderstackConfiguration(EnvironmentIntegrationModel):
    environment = models.OneToOneField(
        Environment, related_name="rudderstack_config", on_delete=models.CASCADE
    )
