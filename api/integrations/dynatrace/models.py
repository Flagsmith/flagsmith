import logging

from django.db import models

from projects.models import Project

logger = logging.getLogger(__name__)


class DynatraceConfiguration(models.Model):
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="dynatrace_config"
    )
    base_url = models.URLField(blank=False, null=False)
    api_key = models.CharField(max_length=100, blank=False, null=False)
