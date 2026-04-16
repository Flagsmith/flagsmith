from django.db import models

from core.models import SoftDeleteExportableModel


class GitLabConfiguration(SoftDeleteExportableModel):
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="gitlab_config",
    )
    gitlab_instance_url = models.URLField(max_length=200)
    access_token = models.CharField(max_length=300)
