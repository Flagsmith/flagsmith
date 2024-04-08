import logging

from django.db import models
from django_lifecycle import (
    AFTER_SAVE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)

from features.models import Feature, FeatureState
from integrations.github.github import generate_data
from integrations.github.tasks import call_github_app_webhook_for_feature_state
from webhooks.webhooks import WebhookEventType

logger = logging.getLogger(__name__)

RESOURCE_TYPES = [
    ("1", "github"),
]

STATUS = [
    ("1", "open"),
    ("2", "closed"),
]


class ExternalResources(LifecycleModelMixin, models.Model):
    url = models.URLField()
    type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS, null=True)
    feature = models.ForeignKey(
        Feature,
        related_name="features",
        on_delete=models.CASCADE,
    )

    @hook(AFTER_SAVE)
    def create_feature_external_resource_added_comment(self):
        if hasattr(self.feature.project.organisation, "github_config"):
            github_configuration = self.feature.project.organisation.github_config

            feature_states = FeatureState.objects.filter(feature_id=self.feature_id)
            feature_data = generate_data(
                github_configuration,
                self.feature_id,
                self.feature.name,
                WebhookEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
                feature_states,
            )

            call_github_app_webhook_for_feature_state.delay(
                args=(
                    feature_data,
                    WebhookEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
                ),
            )
        else:
            organisation_id = self.feature.project.organisation.id
            logger.warning(
                f"No GitHub integration exists for organisation {organisation_id}. Not calling webhooks."
            )

    @hook(BEFORE_DELETE)
    def create_feature_external_resource_removed_comment(self):
        if hasattr(self.feature.project.organisation, "github_config"):
            github_configuration = self.feature.project.organisation.github_config
            feature_data = generate_data(
                github_configuration,
                self.feature_id,
                self.feature.name,
                WebhookEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
                self.url,
            )

            call_github_app_webhook_for_feature_state.delay(
                args=(
                    feature_data,
                    WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
                ),
            )
        else:
            organisation_id = self.feature.project.organisation.id
            logger.warning(
                f"No GitHub integration exists for organisation {organisation_id}. Not calling webhooks."
            )

    class Meta:
        ordering = ("id",)
        unique_together = ("url",)
