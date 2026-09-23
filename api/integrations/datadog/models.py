import logging

from django.db import models

from core.fields import NoSSRFURLField
from integrations.common.models import IntegrationsModel
from projects.models import Project

logger = logging.getLogger(__name__)


class DataDogConfiguration(IntegrationsModel):
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="data_dog_config"
    )
    base_url = NoSSRFURLField(blank=False, null=False)

    use_custom_source = models.BooleanField(default=False)
