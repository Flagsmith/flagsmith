import logging
from typing import Any
from urllib.parse import urlparse

from features.models import Feature
from integrations.github.github import (
    generate_body_comment,
    post_comment_to_github,
)
from task_processor.decorators import register_task_handler
from webhooks.webhooks import WebhookEventType

logger = logging.getLogger(__name__)


def send_post_request(data: dict[str, Any]) -> None:
    feature_name = data["data"]["name"]
    event_type = data["event_type"]
    feature_states = feature_states = (
        data["data"]["feature_states"]
        if "feature_states" in data.get("data", {})
        else None
    )
    installation_id = data["data"]["installation_id"]
    body = generate_body_comment(feature_name, event_type, feature_states)

    if event_type == WebhookEventType.FLAG_UPDATED.value:
        for resource in data.get("feature_external_resources", []):
            url = resource.get("url")
            pathname = urlparse(url).path
            split_url = pathname.split("/")
            post_comment_to_github(
                installation_id, split_url[1], split_url[2], split_url[4], body
            )

    elif event_type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
        url = data["data"]["url"]
        pathname = urlparse(url).path
        split_url = pathname.split("/")
        post_comment_to_github(
            installation_id, split_url[1], split_url[2], split_url[4], body
        )
    else:
        url = data.get("feature_external_resources", [])[
            len(data.get("feature_external_resources", [])) - 1
        ].get("url")
        pathname = urlparse(url).path
        split_url = pathname.split("/")
        post_comment_to_github(
            installation_id, split_url[1], split_url[2], split_url[4], body
        )


@register_task_handler()
def call_github_app_webhook_for_feature_state(
    event_data: dict[str, Any], event_type: str
) -> None:
    if event_type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
        data = {
            "event_type": event_type,
            "data": event_data,
        }
        send_post_request(data)
        return

    feature = Feature.objects.get(id=event_data["id"])
    feature_external_resources = feature.features.all()
    feature_external_resources = [
        {
            "type": resource.type,
            "url": resource.url,
        }
        for resource in feature_external_resources
    ]
    data = {
        "event_type": event_type,
        "data": event_data,
        "feature_external_resources": feature_external_resources,
    }

    if not feature_external_resources:
        logger.debug(
            "No GitHub external resources are associated with this feature id %d. Not calling webhooks.",
            event_data["id"],
        )
        return

    send_post_request(data)
    return
