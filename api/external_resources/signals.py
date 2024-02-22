import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from features.models import FeatureState
from integrations.github.tasks import call_github_app_webhook_for_feature_state
from webhooks.webhooks import WebhookEventType

# noinspection PyUnresolvedReferences
from .models import FeatureExternalResources

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FeatureExternalResources)
def trigger_feature_external_resource_added_webhooks_signal(instance, **kwargs):
    if hasattr(instance.feature.project.organisation, "github_config"):
        github_configuration = instance.feature.project.organisation.github_config

        feature_states = FeatureState.objects.filter(feature_id=instance.feature_id)
        feature_data = {
            "id": instance.feature_id,
            "name": instance.feature.name,
            "feature_states": [],
        }
        feature_data["installation_id"] = github_configuration.installation_id
        feature_data["organisation_id"] = github_configuration.organisation.id

        for feature_state in feature_states:
            feature_env_data = {}
            if feature_state.feature_state_value.string_value is not None:
                feature_env_data[
                    "string_value"
                ] = feature_state.feature_state_value.string_value
            if feature_state.feature_state_value.boolean_value is not None:
                feature_env_data[
                    "boolean_value"
                ] = feature_state.feature_state_value.boolean_value
            if feature_state.feature_state_value.integer_value is not None:
                feature_env_data[
                    "integer_value"
                ] = feature_state.feature_state_value.integer_value

            feature_env_data["environment_name"] = feature_state.environment.name
            feature_env_data["feature_value"] = feature_state.enabled
            if (
                hasattr(feature_state, "feature_segment")
                and feature_state.feature_segment is not None
            ):
                feature_env_data[
                    "segment_name"
                ] = feature_state.feature_segment.segment.name
            feature_data["feature_states"].append(feature_env_data)

        call_github_app_webhook_for_feature_state.delay(
            args=(
                feature_data,
                WebhookEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
            ),
        )
    else:
        print(
            "No GitHub integration exists for organisation %d. Not calling webhooks.",
            instance.feature.project.organisation.id,
        )
        return


@receiver(pre_delete, sender=FeatureExternalResources)
def trigger_feature_external_resource_removed_webhooks_signal(instance, **kwargs):
    if hasattr(instance.feature.project.organisation, "github_config"):
        github_configuration = instance.feature.project.organisation.github_config
        feature_data = {
            "id": instance.feature_id,
            "name": instance.feature.name,
            "url": instance.external_resource.url,
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
        print(
            "No GitHub integration exists for organisation %d. Not calling webhooks.",
            instance.feature.project.organisation.id,
        )
        return
