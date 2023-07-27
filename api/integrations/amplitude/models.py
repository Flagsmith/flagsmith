from django.db import models

from environments.models import Environment
from integrations.amplitude.constants import DEFAULT_AMPLITUDE_API_URL
from integrations.common.models import EnvironmentIntegrationModel


class AmplitudeConfiguration(EnvironmentIntegrationModel):
    base_url = models.URLField(default=DEFAULT_AMPLITUDE_API_URL)
    environment = models.OneToOneField(
        Environment, related_name="amplitude_config", on_delete=models.CASCADE
    )
