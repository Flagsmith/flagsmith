import logging

from django.db import models
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_CREATE,
    AFTER_UPDATE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)

from core.models import SoftDeleteExportableModel
from integrations.gitlab.constants import GITLAB_TAG_COLOR

logger: logging.Logger = logging.getLogger(name=__name__)


class GitLabConfiguration(LifecycleModelMixin, SoftDeleteExportableModel):  # type: ignore[misc]
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="gitlab_project",
    )
    gitlab_instance_url = models.URLField(
        max_length=200,
        blank=False,
        null=False,
        help_text="Base URL of the GitLab instance, e.g. https://gitlab.com",
    )
    access_token = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        help_text="GitLab Group or Project Access Token with api scope",
    )
    webhook_secret = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        help_text="Secret token for validating incoming GitLab webhooks",
    )
    gitlab_project_id = models.IntegerField(
        blank=True,
        null=True,
        help_text="GitLab's numeric project ID",
    )
    project_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="GitLab project path with namespace, e.g. my-group/my-project",
    )
    tagging_enabled = models.BooleanField(default=False)

    @staticmethod
    def has_gitlab_configuration(project_id: int) -> bool:
        return GitLabConfiguration.objects.filter(  # type: ignore[no-any-return]
            project_id=project_id
        ).exists()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project"],
                name="gitlabconf_project_id_idx",
                condition=models.Q(deleted_at__isnull=True),
            )
        ]
        ordering = ("id",)

    @hook(BEFORE_DELETE)  # type: ignore[misc]
    def delete_feature_external_resources(self) -> None:
        import re

        from features.feature_external_resources.models import (
            FeatureExternalResource,
            ResourceType,
        )

        if self.project_name:
            pattern = re.escape(f"/{self.project_name}/-/")
            FeatureExternalResource.objects.filter(
                feature_id__in=self.project.features.values_list("id", flat=True),
                type__in=[
                    ResourceType.GITLAB_ISSUE,
                    ResourceType.GITLAB_MR,
                ],
                url__regex=pattern,
            ).delete()

    @hook(AFTER_CREATE)  # type: ignore[misc]
    @hook(AFTER_UPDATE, when="tagging_enabled", has_changed=True, was=False)  # type: ignore[misc]
    def create_gitlab_tags(self) -> None:
        from integrations.gitlab.constants import (
            GitLabTag,
            gitlab_tag_description,
        )
        from projects.tags.models import Tag, TagType

        for tag_label in GitLabTag:
            Tag.objects.get_or_create(
                color=GITLAB_TAG_COLOR,
                description=gitlab_tag_description[tag_label.value],
                label=tag_label.value,
                project=self.project,
                is_system_tag=True,
                type=TagType.GITLAB.value,
            )
