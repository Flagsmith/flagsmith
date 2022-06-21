import logging

from django.db import models

from integrations.common.models import IntegrationsModel
from projects.models import Project

logger = logging.getLogger(__name__)


class NewRelicConfiguration(IntegrationsModel):
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="new_relic_config"
    )
    app_id = models.CharField(max_length=100, blank=False, null=False)

    def natural_key(self):
        return self.project_id, self.api_key
