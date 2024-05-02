import logging

from core.models import SoftDeleteExportableModel
from django.db import models
from django_lifecycle import BEFORE_DELETE, LifecycleModelMixin, hook

from organisations.models import Organisation

logger: logging.Logger = logging.getLogger(name=__name__)


class GithubConfiguration(SoftDeleteExportableModel):
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="github_config"
    )
    installation_id = models.CharField(max_length=100, blank=False, null=False)

    @staticmethod
    def has_github_configuration(organisation_id: int) -> bool:
        return GithubConfiguration.objects.filter(
            organisation_id=organisation_id
        ).exists()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organisation",
                ],
                name="githubconf_organisation_id_idx",
                condition=models.Q(deleted_at__isnull=True),
            )
        ]


class GithubRepository(LifecycleModelMixin, SoftDeleteExportableModel):
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

    @hook(BEFORE_DELETE)
    def delete_feature_external_resources(
        self,
    ) -> None:
        from features.feature_external_resources.models import (
            FeatureExternalResource,
        )

        FeatureExternalResource.objects.filter(
            feature_id__in=self.project.features.values_list("id", flat=True),
            type__in=[
                FeatureExternalResource.ResourceType.GITHUB_ISSUE,
                FeatureExternalResource.ResourceType.GITHUB_PR,
            ],
        ).delete()
