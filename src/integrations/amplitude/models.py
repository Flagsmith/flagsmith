from django.db import models

from environments.models import Environment
from integrations.common.models import IntegrationsModel


class AmplitudeConfiguration(IntegrationsModel):
    environment = models.OneToOneField(
        Environment, related_name="amplitude_config", on_delete=models.CASCADE
    )
