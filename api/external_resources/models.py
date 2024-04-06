from django.db import models
from django_lifecycle import (
    AFTER_SAVE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)

from features.models import Feature, FeatureState
from integrations.github.tasks import call_github_app_webhook_for_feature_state
from webhooks.webhooks import WebhookEventType

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
            feature_data = {
                "id": self.feature_id,
                "name": self.feature.name,
                "feature_states": [],
            }
            feature_data["installation_id"] = github_configuration.installation_id
            feature_data["organisation_id"] = github_configuration.organisation.id

            for feature_state in feature_states:
                feature_env_data = {}
                if feature_state.feature_state_value.string_value is not None:
                    feature_env_data["string_value"] = (
                        feature_state.feature_state_value.string_value
                    )
                if feature_state.feature_state_value.boolean_value is not None:
                    feature_env_data["boolean_value"] = (
                        feature_state.feature_state_value.boolean_value
                    )
                if feature_state.feature_state_value.integer_value is not None:
                    feature_env_data["integer_value"] = (
                        feature_state.feature_state_value.integer_value
                    )

                feature_env_data["environment_name"] = feature_state.environment.name
                feature_env_data["feature_value"] = feature_state.enabled
                if (
                    hasattr(feature_state, "feature_segment")
                    and feature_state.feature_segment is not None
                ):
                    feature_env_data["segment_name"] = (
                        feature_state.feature_segment.segment.name
                    )
                feature_data["feature_states"].append(feature_env_data)

            call_github_app_webhook_for_feature_state.delay(
                args=(
                    feature_data,
                    WebhookEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
                ),
            )
        else:
            organisation_id = self.feature.project.organisation.id
            print(
                f"No GitHub integration exists for organisation {organisation_id}. Not calling webhooks."
            )

    @hook(BEFORE_DELETE)
    def create_feature_external_resource_removed_comment(self):
        if hasattr(self.feature.project.organisation, "github_config"):
            github_configuration = self.feature.project.organisation.github_config
            feature_data = {
                "id": self.feature_id,
                "name": self.feature.name,
                "url": self.url,
            }
            feature_data["installation_id"] = github_configuration.installation_id
            feature_data["organisation_id"] = github_configuration.organisation.id

            call_github_app_webhook_for_feature_state.delay(
                args=(
                    feature_data,
                    WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
                ),
            )
        else:
            organisation_id = self.feature.project.organisation.id
            print(
                f"No GitHub integration exists for organisation {organisation_id}. Not calling webhooks."
            )

    class Meta:
        ordering = ("id",)
        unique_together = ("url",)
