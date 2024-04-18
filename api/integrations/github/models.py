import logging

from core.models import SoftDeleteExportableModel
from django.db import models

from organisations.models import Organisation

logger: logging.Logger = logging.getLogger(name=__name__)


class GithubConfiguration(SoftDeleteExportableModel):
    organisation = models.OneToOneField(
        Organisation, on_delete=models.CASCADE, related_name="github_config"
    )
    installation_id = models.CharField(max_length=100, blank=False, null=False)

    @staticmethod
    def has_github_configuration(organisation_id: int) -> bool:
        return GithubConfiguration.objects.filter(
            organisation_id=organisation_id
        ).exists()


class GithubRepository(SoftDeleteExportableModel):
    github_configuration = models.ForeignKey(
        GithubConfiguration, related_name="repository_config", on_delete=models.CASCADE
    )
    repository_owner = models.CharField(max_length=100, blank=False, null=False)
    repository_name = models.CharField(max_length=100, blank=False, null=False)
    project = models.ForeignKey(
        "projects.Project",
        related_name="github_project",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "github_configuration",
                    "project",
                    "repository_owner",
                    "repository_name",
                ],
                name="unique_repository_data",
            )
        ]
