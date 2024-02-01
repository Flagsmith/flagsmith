import logging
from typing import Any

from features.models import Feature
from integrations.github.github import GithubWrapper
from organisations.models import Organisation
from task_processor.decorators import register_task_handler
from webhooks.webhooks import WebhookEventType

logger = logging.getLogger(__name__)


@register_task_handler()
def call_github_app_webhook_for_feature_state(
    organisation: Organisation, event_data: dict[str, Any], event_type: WebhookEventType
):
    github_configuration = organisation.github_config
    if not github_configuration:
        logger.debug(
            "No GitHub integration exists for organisation %d. Not calling webhooks.",
            organisation.id,
        )
        return

    feature = Feature.objects.get(id=event_data["new_state"]["feature"]["id"])
    feature_external_resources = feature.featureexternalresources_set.all()
    external_resources = [
        {
            "type": resource.external_resource.type,
            "url": resource.external_resource.url,
        }
        for resource in feature_external_resources
    ]

    print(
        "DEBUG: call_github_app_webhook_for_feature_state: external_resources",
        external_resources,
    )

    if not feature_external_resources:
        logger.debug(
            "No GitHub external resources are associated to this feature id %d. Not calling webhooks.",
            event_data["new_state"]["feature"]["id"],
        )
        return

    github = GithubWrapper(
        github_configuration,
    )

    github.track_event(
        event=event_data, event_type=event_type, external_resources=external_resources
    )
