import logging
from dataclasses import asdict

from django.db.models.signals import post_save
from django.dispatch import receiver

from integrations.github.github import GithubData, generate_data
from integrations.github.tasks import call_github_app_webhook_for_feature_state
from organisations.models import Organisation
from webhooks.webhooks import WebhookEventType

# noinspection PyUnresolvedReferences
from .models import FeatureState
from .tasks import trigger_feature_state_change_webhooks

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FeatureState)
def trigger_feature_state_change_webhooks_signal(instance, **kwargs):
    # Enqueue Github integration tasks if feature has GitHub external resources
    if (
        not instance.identity_id
        and not instance.feature_segment
        and instance.feature.external_resources.exists()
        and instance.environment.project.github_project.exists()
        and hasattr(instance.environment.project.organisation, "github_config")
    ):
        github_configuration = (
            Organisation.objects.prefetch_related("github_config")
            .get(id=instance.environment.project.organisation_id)
            .github_config.first()
        )
        feature_states = []
        feature_states.append(instance)

        feature_data: GithubData = generate_data(
            github_configuration=github_configuration,
            feature_id=instance.feature.id,
            feature_name=instance.feature.name,
            type=WebhookEventType.FLAG_UPDATED.value,
            feature_states=feature_states,
        )

        call_github_app_webhook_for_feature_state.delay(
            args=(asdict(feature_data),),
        )

    if instance.environment_feature_version_id:
        return
    trigger_feature_state_change_webhooks(instance)
