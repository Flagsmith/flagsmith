from django.db import models

from core.fields import NoSSRFURLField
from environments.models import Environment
from integrations.amplitude.constants import DEFAULT_AMPLITUDE_API_URL
from integrations.common.models import EnvironmentIntegrationModel


class AmplitudeConfiguration(EnvironmentIntegrationModel):
    base_url = NoSSRFURLField(default=DEFAULT_AMPLITUDE_API_URL)
    environment = models.OneToOneField(
        Environment, related_name="amplitude_config", on_delete=models.CASCADE
    )
