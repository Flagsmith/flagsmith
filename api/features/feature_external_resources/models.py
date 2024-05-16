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
from organisations.models import Organisation
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
    def execute_after_save_actions(self):
        # Add a comment to GitHub Issue/PR when feature is linked to the GH external resource
        if (
            github_configuration := Organisation.objects.prefetch_related(
                "github_config"
            )
            .get(id=self.feature.project.organisation_id)
            .github_config.first()
        ):
            feature_states = FeatureState.objects.filter(
                feature_id=self.feature_id, identity_id__isnull=True
            )
            feature_data: GithubData = generate_data(
                github_configuration=github_configuration,
                feature=self.feature,
                type=WebhookEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
                feature_states=feature_states,
            )

            call_github_app_webhook_for_feature_state.delay(
                args=(asdict(feature_data),),
            )

    @hook(BEFORE_DELETE)
    def execute_before_save_actions(self) -> None:
        # Add a comment to GitHub Issue/PR when feature is unlinked to the GH external resource
        if (
            github_configuration := Organisation.objects.prefetch_related(
                "github_config"
            )
            .get(id=self.feature.project.organisation_id)
            .github_config.first()
        ):
            feature_data: GithubData = generate_data(
                github_configuration=github_configuration,
                feature=self.feature,
                type=WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
                url=self.url,
            )

            call_github_app_webhook_for_feature_state.delay(
                args=(asdict(feature_data),),
            )
