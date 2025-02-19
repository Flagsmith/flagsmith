import logging
import re

from core.models import SoftDeleteExportableModel
from django.db import models
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_CREATE,
    AFTER_UPDATE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)

from integrations.github.constants import GITHUB_TAG_COLOR
from organisations.models import Organisation

logger: logging.Logger = logging.getLogger(name=__name__)


class GithubConfiguration(SoftDeleteExportableModel):
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="github_config"
    )
    installation_id = models.CharField(max_length=100, blank=False, null=False)

    @staticmethod
    def has_github_configuration(organisation_id: int) -> bool:
        return GithubConfiguration.objects.filter(  # type: ignore[no-any-return]
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
        ordering = ("id",)


class GitHubRepository(LifecycleModelMixin, SoftDeleteExportableModel):  # type: ignore[misc]
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
    tagging_enabled = models.BooleanField(default=False)

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
                condition=models.Q(deleted_at__isnull=True),
            )
        ]
        ordering = ("id",)

    @hook(BEFORE_DELETE)  # type: ignore[misc]
    def delete_feature_external_resources(
        self,
    ) -> None:
        from features.feature_external_resources.models import (
            FeatureExternalResource,
            ResourceType,
        )

        pattern = re.escape(f"/{self.repository_owner}/{self.repository_name}/")

        FeatureExternalResource.objects.filter(
            feature_id__in=self.project.features.values_list("id", flat=True),
            type__in=[
                ResourceType.GITHUB_ISSUE,
                ResourceType.GITHUB_PR,
            ],
            # Filter by url containing the repository owner and name
            url__regex=pattern,
        ).delete()

    @hook(AFTER_CREATE)  # type: ignore[misc]
    @hook(AFTER_UPDATE, when="tagging_enabled", has_changed=True, was=False)  # type: ignore[misc]
    def create_github_tags(
        self,
    ) -> None:
        from integrations.github.constants import (
            GitHubTag,
            github_tag_description,
        )
        from projects.tags.models import Tag, TagType

        for tag_label in GitHubTag:
            tag, created = Tag.objects.get_or_create(
                color=GITHUB_TAG_COLOR,
                description=github_tag_description[tag_label.value],
                label=tag_label.value,
                project=self.project,
                is_system_tag=True,
                type=TagType.GITHUB.value,
            )
