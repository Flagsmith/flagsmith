import logging
from typing import Any, List
from urllib.parse import urlparse

from task_processor.decorators import register_task_handler  # type: ignore[import-untyped]

from features.models import Feature
from integrations.github.client import post_comment_to_github
from integrations.github.constants import GitHubEventType
from integrations.github.dataclasses import CallGithubData

logger = logging.getLogger(__name__)


def send_post_request(data: CallGithubData) -> None:
    from integrations.github.github import generate_body_comment

    feature_name = data.github_data.feature_name
    feature_id = data.github_data.feature_id
    project_id = data.github_data.project_id
    event_type = data.event_type
    feature_states = (
        data.github_data.feature_states if data.github_data.feature_states else None
    )
    installation_id = data.github_data.installation_id
    segment_name: str | None = data.github_data.segment_name
    body = generate_body_comment(
        feature_name, event_type, project_id, feature_id, feature_states, segment_name  # type: ignore[arg-type]
    )

    if (
        event_type == GitHubEventType.FLAG_UPDATED.value
        or event_type == GitHubEventType.FLAG_DELETED.value
        or event_type == GitHubEventType.FLAG_UPDATED_FROM_GHA.value
    ):
        for resource in data.feature_external_resources:
            url = resource.get("url")
            pathname = urlparse(url).path
            split_url = pathname.split("/")  # type: ignore[arg-type]
            post_comment_to_github(
                installation_id, split_url[1], split_url[2], split_url[4], body  # type: ignore[arg-type]
            )

    elif event_type == GitHubEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
        url = data.github_data.url
        pathname = urlparse(url).path  # type: ignore[assignment]
        split_url = pathname.split("/")  # type: ignore[arg-type]
        post_comment_to_github(
            installation_id, split_url[1], split_url[2], split_url[4], body  # type: ignore[arg-type]
        )
    else:
        url = data.feature_external_resources[
            len(data.feature_external_resources) - 1
        ].get("url")
        pathname = urlparse(url).path
        split_url = pathname.split("/")  # type: ignore[arg-type]
        post_comment_to_github(
            installation_id, split_url[1], split_url[2], split_url[4], body  # type: ignore[arg-type]
        )


@register_task_handler()  # type: ignore[misc]
def call_github_app_webhook_for_feature_state(event_data: dict[str, Any]) -> None:

    from features.feature_external_resources.models import (
        FeatureExternalResource,
    )
    from integrations.github.github import GithubData  # type: ignore[attr-defined]

    github_event_data = GithubData.from_dict(event_data)

    def generate_feature_external_resources(
        feature_external_resources: List[FeatureExternalResource],
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": resource.type,
                "url": resource.url,
            }
            for resource in feature_external_resources
        ]

    if (
        github_event_data.type == GitHubEventType.FLAG_DELETED.value
        or github_event_data.type == GitHubEventType.SEGMENT_OVERRIDE_DELETED.value
    ):
        feature_external_resources = generate_feature_external_resources(
            list(
                FeatureExternalResource.objects.filter(
                    feature_id=github_event_data.feature_id
                )
            )
        )
        data = CallGithubData(
            event_type=github_event_data.type,
            github_data=github_event_data,
            feature_external_resources=feature_external_resources,
        )
        send_post_request(data)
        return

    if (
        github_event_data.type
        == GitHubEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
    ):
        data = CallGithubData(
            event_type=github_event_data.type,
            github_data=github_event_data,
            feature_external_resources=None,  # type: ignore[arg-type]
        )
        send_post_request(data)
        return

    feature = Feature.objects.get(id=github_event_data.feature_id)
    feature_external_resources = generate_feature_external_resources(
        feature.external_resources.all()
    )
    data = CallGithubData(
        event_type=github_event_data.type,
        github_data=github_event_data,
        feature_external_resources=feature_external_resources,
    )

    if not feature_external_resources:
        logger.debug(
            "No GitHub external resources are associated with this feature id %d. Not calling webhooks.",
            github_event_data.feature_id,
        )
        return

    send_post_request(data)
    return
