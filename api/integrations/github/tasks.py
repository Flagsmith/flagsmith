import json
import logging
from enum import Enum
from typing import Any

import requests

from features.models import Feature
from task_processor.decorators import register_task_handler
from webhooks.webhooks import WebhookEventType

logger = logging.getLogger(__name__)


BASE_URL = "http://localhost:3000/api/flagsmith-webhook"


class GithubResourceType(Enum):
    GITHUB_ISSUE = "Github Issue"
    GITHUB_PR = "Github PR"


def send_post_request(data: dict[str, Any]) -> None:
    response = requests.post(
        str(BASE_URL),
        data=json.dumps(data),
        headers={"content-type": "application/json"},
        timeout=10,
    )

    print("DEBUG: Sent event to GitHub. Response code was:", response)
    logger.debug("Sent event to GitHub. Response code was %s" % response.status_code)


@register_task_handler()
def call_github_app_webhook_for_feature_state(
    event_data: dict[str, Any], event_type: str
):
    if event_type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
        data = {
            "event_type": event_type,
            "data": event_data,
        }

        send_post_request(data)
        return

    feature = Feature.objects.get(id=event_data["id"])
    feature_external_resources = feature.featureexternalresources_set.all()
    external_resources = [
        {
            "type": resource.external_resource.type,
            "url": resource.external_resource.url,
        }
        for resource in feature_external_resources
    ]
    data = {
        "event_type": event_type,
        "data": event_data,
        "external_resources": external_resources,
    }

    if not feature_external_resources:
        logger.debug(
            "No GitHub external resources are associated with this feature id %d. Not calling webhooks.",
            event_data["new_state"]["feature"]["id"],
        )
        return

    send_post_request(data)
    return
