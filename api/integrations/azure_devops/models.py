from django.db import models

from core.models import SoftDeleteExportableModel


class AzureDevOpsConfiguration(SoftDeleteExportableModel):
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="azure_devops_config",
    )
    organisation_url = models.URLField(max_length=300)
    personal_access_token = models.CharField(max_length=300)
    labeling_enabled = models.BooleanField(default=False)
    tagging_enabled = models.BooleanField(default=False)
