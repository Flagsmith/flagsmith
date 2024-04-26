import logging
from dataclasses import asdict

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_lifecycle import (
    AFTER_SAVE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)

from features.models import Feature, FeatureState
from integrations.github.github import GithubData, generate_data
from integrations.github.tasks import call_github_app_webhook_for_feature_state
from webhooks.webhooks import WebhookEventType

logger = logging.getLogger(__name__)


class FeatureExternalResource(LifecycleModelMixin, models.Model):
    class ResourceType(models.TextChoices):
        # GitHub external resource types
        GITHUB_ISSUE = "GITHUB_ISSUE", _("GitHub Issue")
        GITHUB_PR = "GITHUB_PR", _("GitHub PR")

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
    def exectute_after_save_actions(self):
        # Add a comment to GitHub Issue/PR when feature is linked to the GH external resource
        if hasattr(self.feature.project.organisation, "github_config"):
            github_configuration = self.feature.project.organisation.github_config

            feature_states = FeatureState.objects.filter(feature_id=self.feature_id)
            feature_data: GithubData = generate_data(
                github_configuration,
                self.feature_id,
                self.feature.name,
                WebhookEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
                feature_states,
            )

            call_github_app_webhook_for_feature_state.delay(
                args=(asdict(feature_data),),
            )

    @hook(BEFORE_DELETE)
    def execute_before_save_actions(self) -> None:
        # Add a comment to GitHub Issue/PR when feature is unlinked to the GH external resource
        if hasattr(self.feature.project.organisation, "github_config"):
            github_configuration = self.feature.project.organisation.github_config
            feature_data: GithubData = generate_data(
                github_configuration=github_configuration,
                feature_id=self.feature_id,
                feature_name=self.feature.name,
                type=WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
                url=self.url,
            )

            call_github_app_webhook_for_feature_state.delay(
                args=(asdict(feature_data),),
            )
