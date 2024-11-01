import json
import logging
import re

from django.db import models
from django.db.models import Q
from django_lifecycle import (
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


class FeatureExternalResource(LifecycleModelMixin, models.Model):
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
    def execute_after_save_actions(self):
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
            owner, repo = url_match.groups()

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
                organisation_id=self.feature.project.organisation_id,
                type=GitHubEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
                feature=self.feature,
                segment_name=None,
                url=None,
                feature_states=feature_states,
            )

    @hook(BEFORE_DELETE)
    def execute_before_save_actions(self) -> None:
        # Add a comment to GitHub Issue/PR when feature is unlinked to the GH external resource
        if (
            Organisation.objects.prefetch_related("github_config")
            .get(id=self.feature.project.organisation_id)
            .github_config.first()
        ):

            call_github_task(
                organisation_id=self.feature.project.organisation_id,
                type=GitHubEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
                feature=self.feature,
                segment_name=None,
                url=self.url,
                feature_states=None,
            )
