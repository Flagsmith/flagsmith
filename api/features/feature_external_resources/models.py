import json
import logging
import re

from django.db import models
from django.db.models import Q
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_DELETE,
    AFTER_SAVE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)

from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.github.constants import GitHubEventType, GitHubTag
from integrations.github.github import call_github_task
from integrations.github.models import GitHubRepository
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


GITLAB_RESOURCE_TYPES: tuple[ResourceType, ...] = (
    ResourceType.GITLAB_ISSUE,
    ResourceType.GITLAB_MR,
)


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

    @hook(AFTER_SAVE, when="type", is_now="GITHUB_ISSUE")
    @hook(AFTER_SAVE, when="type", is_now="GITHUB_PR")
    def notify_github_on_link(self):  # type: ignore[no-untyped-def]
        # Tag the feature with the external resource type
        metadata = json.loads(self.metadata) if self.metadata else {}
        state = metadata.get("state", "open")

        # Add a comment to GitHub Issue/PR when feature is linked to the GH external resource
        # and tag the feature with the corresponding tag if tagging is enabled
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

            feature_states: list[FeatureState] = []

            environments = Environment.objects.filter(
                project_id=self.feature.project_id
            )

            for environment in environments:
                q = Q(
                    feature_id=self.feature_id,
                    identity__isnull=True,
                )
                feature_states.extend(
                    FeatureState.objects.get_live_feature_states(
                        environment=environment, additional_filters=q
                    )
                )

            call_github_task(
                organisation_id=self.feature.project.organisation_id,  # type: ignore[arg-type]
                type=GitHubEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
                feature=self.feature,
                segment_name=None,
                url=None,
                feature_states=feature_states,
            )

    @hook(AFTER_SAVE, when="type", is_now="GITLAB_ISSUE")  # type: ignore[misc]
    @hook(AFTER_SAVE, when="type", is_now="GITLAB_MR")  # type: ignore[misc]
    def apply_gitlab_tag(self) -> None:
        from integrations.gitlab.services import apply_initial_tag

        apply_initial_tag(self)

    @hook(AFTER_DELETE, when="type", is_now="GITLAB_ISSUE")  # type: ignore[misc]
    @hook(AFTER_DELETE, when="type", is_now="GITLAB_MR")  # type: ignore[misc]
    def deregister_gitlab_webhook(self) -> None:
        from integrations.gitlab.models import GitLabConfiguration
        from integrations.gitlab.services import parse_project_path
        from integrations.gitlab.tasks import (
            deregister_gitlab_webhook as deregister_task,
        )

        project_path = parse_project_path(self.url)
        if project_path is None:
            return
        config = GitLabConfiguration.objects.filter(
            project=self.feature.project,
        ).first()
        if config is None:
            return
        deregister_task.delay(args=(config.id, project_path))

    @hook(BEFORE_DELETE, when="type", is_now="GITHUB_ISSUE")  # type: ignore[misc]
    @hook(BEFORE_DELETE, when="type", is_now="GITHUB_PR")  # type: ignore[misc]
    def notify_github_on_unlink(self) -> None:
        # Add a comment to GitHub Issue/PR when feature is unlinked to the GH external resource
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
