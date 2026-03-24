import json
import logging
import re

from django.db import models
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_SAVE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)

from features.models import Feature
from integrations.github.constants import GitHubEventType, GitHubTag
from integrations.gitlab.constants import GitLabEventType, GitLabTag
from organisations.models import Organisation
from projects.tags.models import Tag, TagType

logger = logging.getLogger(__name__)


class ResourceType(models.TextChoices):
    # GitHub external resource types
    GITHUB_ISSUE = "GITHUB_ISSUE", "GitHub Issue"
    GITHUB_PR = "GITHUB_PR", "GitHub PR"
    # GitLab external resource types
    GITLAB_ISSUE = "GITLAB_ISSUE", "GitLab Issue"
    GITLAB_MR = "GITLAB_MR", "GitLab MR"


tag_by_type_and_state = {
    ResourceType.GITHUB_ISSUE.value: {
        "open": GitHubTag.ISSUE_OPEN.value,
        "closed": GitHubTag.ISSUE_CLOSED.value,
    },
    ResourceType.GITHUB_PR.value: {
        "open": GitHubTag.PR_OPEN.value,
        "closed": GitHubTag.PR_CLOSED.value,
        "merged": GitHubTag.PR_MERGED.value,
        "draft": GitHubTag.PR_DRAFT.value,
    },
    ResourceType.GITLAB_ISSUE.value: {
        "opened": GitLabTag.ISSUE_OPEN.value,
        "closed": GitLabTag.ISSUE_CLOSED.value,
    },
    ResourceType.GITLAB_MR.value: {
        "opened": GitLabTag.MR_OPEN.value,
        "closed": GitLabTag.MR_CLOSED.value,
        "merged": GitLabTag.MR_MERGED.value,
    },
}


class FeatureExternalResource(LifecycleModelMixin, models.Model):  # type: ignore[misc]
    url = models.URLField()
    type = models.CharField(max_length=20, choices=ResourceType.choices)

    # JSON filed containing any metadata related to the external resource
    metadata = models.TextField(null=True)
    feature = models.ForeignKey(
        Feature,
        related_name="external_resources",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=["feature", "url"], name="unique_feature_url_constraint"
            )
        ]
        indexes = [
            models.Index(fields=["type"]),
        ]

    @hook(AFTER_SAVE)
    def execute_after_save_actions(self):  # type: ignore[no-untyped-def]
        metadata = json.loads(self.metadata) if self.metadata else {}
        state = metadata.get("state", "open")

        if self.type in (ResourceType.GITHUB_ISSUE, ResourceType.GITHUB_PR):
            self._handle_github_after_save(state)
        elif self.type in (ResourceType.GITLAB_ISSUE, ResourceType.GITLAB_MR):
            self._handle_gitlab_after_save(state)

    def _handle_github_after_save(self, state: str) -> None:
        from integrations.github.github import call_github_task
        from integrations.github.models import GitHubRepository

        if (
            github_configuration := Organisation.objects.prefetch_related(
                "github_config"
            )
            .get(id=self.feature.project.organisation_id)
            .github_config.first()
        ):
            if self.type == "GITHUB_PR":
                pattern = r"github.com/([^/]+)/([^/]+)/pull/\d+$"
            elif self.type == "GITHUB_ISSUE":
                pattern = r"github.com/([^/]+)/([^/]+)/issues/\d+$"

            url_match = re.search(pattern, self.url)
            owner, repo = url_match.groups()  # type: ignore[union-attr]

            github_repo = GitHubRepository.objects.get(
                github_configuration=github_configuration.id,
                project=self.feature.project,
                repository_owner=owner,
                repository_name=repo,
            )
            if github_repo.tagging_enabled:
                github_tag, _ = Tag.objects.get_or_create(
                    label=tag_by_type_and_state[self.type][state],
                    project=self.feature.project,
                    is_system_tag=True,
                    type=TagType.GITHUB.value,
                )
                self.feature.tags.add(github_tag)
                self.feature.save()

            from integrations.vcs.helpers import collect_feature_states_for_resource

            feature_states = collect_feature_states_for_resource(
                feature_id=self.feature_id,
                project_id=self.feature.project_id,
            )

            call_github_task(
                organisation_id=self.feature.project.organisation_id,  # type: ignore[arg-type]
                type=GitHubEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
                feature=self.feature,
                segment_name=None,
                url=None,
                feature_states=feature_states,
            )

    def _handle_gitlab_after_save(self, state: str) -> None:
        from integrations.gitlab.gitlab import call_gitlab_task
        from integrations.gitlab.models import GitLabConfiguration

        try:
            gitlab_config = GitLabConfiguration.objects.get(
                project=self.feature.project,
                deleted_at__isnull=True,
            )
        except GitLabConfiguration.DoesNotExist:
            return

        if gitlab_config.tagging_enabled:
            gitlab_tag, _ = Tag.objects.get_or_create(
                label=tag_by_type_and_state[self.type][state],
                project=self.feature.project,
                is_system_tag=True,
                type=TagType.GITLAB.value,
            )
            self.feature.tags.add(gitlab_tag)
            self.feature.save()

        from integrations.vcs.helpers import collect_feature_states_for_resource

        feature_states = collect_feature_states_for_resource(
            feature_id=self.feature_id,
            project_id=self.feature.project_id,
        )

        call_gitlab_task(
            project_id=self.feature.project_id,
            type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
            feature=self.feature,
            segment_name=None,
            url=None,
            feature_states=feature_states,
        )

    @hook(BEFORE_DELETE)  # type: ignore[misc]
    def execute_before_save_actions(self) -> None:
        if self.type in (ResourceType.GITHUB_ISSUE, ResourceType.GITHUB_PR):
            from integrations.github.github import call_github_task

            if (
                Organisation.objects.prefetch_related("github_config")
                .get(id=self.feature.project.organisation_id)
                .github_config.first()
            ):
                call_github_task(
                    organisation_id=self.feature.project.organisation_id,  # type: ignore[arg-type]
                    type=GitHubEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
                    feature=self.feature,
                    segment_name=None,
                    url=self.url,
                    feature_states=None,
                )
        elif self.type in (ResourceType.GITLAB_ISSUE, ResourceType.GITLAB_MR):
            from integrations.gitlab.gitlab import call_gitlab_task
            from integrations.gitlab.models import GitLabConfiguration

            try:
                GitLabConfiguration.objects.get(
                    project=self.feature.project,
                    deleted_at__isnull=True,
                )
            except GitLabConfiguration.DoesNotExist:
                return

            call_gitlab_task(
                project_id=self.feature.project_id,
                type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
                feature=self.feature,
                segment_name=None,
                url=self.url,
                feature_states=None,
            )
