import logging
import re
from typing import Any, List
from urllib.parse import urlparse

from task_processor.decorators import register_task_handler

from features.models import Feature
from integrations.gitlab.client import post_comment_to_gitlab
from integrations.gitlab.constants import GitLabEventType
from integrations.gitlab.dataclasses import CallGitLabData

logger = logging.getLogger(__name__)


def _resolve_resource_urls_for_event(data: CallGitLabData) -> list[str]:
    """Return the list of resource URLs to post a comment to, based on event type."""
    event_type = data.event_type

    if (
        event_type == GitLabEventType.FLAG_UPDATED.value
        or event_type == GitLabEventType.FLAG_DELETED.value
    ):
        return [r.get("url", "") for r in data.feature_external_resources]

    if event_type == GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
        if data.gitlab_data.url:
            return [data.gitlab_data.url]
        return []

    # Default: use the last linked resource (e.g. newly added resource)
    if data.feature_external_resources:
        return [data.feature_external_resources[-1].get("url", "")]
    return []


def _post_to_resource(
    resource_url: str,
    instance_url: str,
    access_token: str,
    body: str,
) -> None:
    """Parse a GitLab resource URL and post a comment."""
    from integrations.gitlab.models import GitLabConfiguration

    parsed = urlparse(resource_url)
    path = parsed.path

    # Determine resource type from URL path
    if "/-/merge_requests/" in path:
        resource_type = "merge_requests"
        iid_match = re.search(r"/-/merge_requests/(\d+)", path)
    elif "/-/issues/" in path or "/-/work_items/" in path:
        resource_type = "issues"
        iid_match = re.search(r"/-/(?:issues|work_items)/(\d+)", path)
    else:
        logger.warning("Unknown GitLab resource URL format: %s", resource_url)
        return

    if not iid_match:
        return

    resource_iid = int(iid_match.group(1))

    # Extract project path from URL (everything between host and /-/)
    project_path_match = re.search(r"^/([^/-]+(?:/[^/-]+)*)/-/", path)
    if not project_path_match:
        return
    project_path = project_path_match.group(1)

    # Look up the GitLab project ID from our repository model
    try:
        gitlab_config = GitLabConfiguration.objects.get(project_name=project_path)
        gitlab_project_id = gitlab_config.gitlab_project_id
    except GitLabConfiguration.DoesNotExist:
        logger.warning(
            "No GitLabConfiguration found for project path: %s", project_path
        )
        return

    post_comment_to_gitlab(
        instance_url=instance_url,
        access_token=access_token,
        gitlab_project_id=gitlab_project_id,
        resource_type=resource_type,
        resource_iid=resource_iid,
        body=body,
    )


def send_post_request(data: CallGitLabData) -> None:
    from integrations.gitlab.gitlab import generate_body_comment

    feature_name = data.gitlab_data.feature_name
    feature_id = data.gitlab_data.feature_id
    project_id = data.gitlab_data.project_id
    event_type = data.event_type
    feature_states = data.gitlab_data.feature_states or []
    instance_url = data.gitlab_data.gitlab_instance_url
    access_token = data.gitlab_data.access_token
    segment_name = data.gitlab_data.segment_name

    body = generate_body_comment(
        name=feature_name,
        event_type=event_type,
        project_id=project_id,
        feature_id=feature_id,
        feature_states=feature_states,
        segment_name=segment_name,
    )

    for resource_url in _resolve_resource_urls_for_event(data):
        _post_to_resource(
            resource_url=resource_url,
            instance_url=instance_url,
            access_token=access_token,
            body=body,
        )


@register_task_handler()
def call_gitlab_app_webhook_for_feature_state(event_data: dict[str, Any]) -> None:
    from features.feature_external_resources.models import (
        FeatureExternalResource,
        ResourceType,
    )
    from integrations.gitlab.dataclasses import GitLabData as GitLabDataClass

    gitlab_event_data = GitLabDataClass.from_dict(event_data)

    def generate_feature_external_resources(
        feature_external_resources: List[FeatureExternalResource],
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": resource.type,
                "url": resource.url,
            }
            for resource in feature_external_resources
            if resource.type in (ResourceType.GITLAB_ISSUE, ResourceType.GITLAB_MR)
        ]

    if (
        gitlab_event_data.type == GitLabEventType.FLAG_DELETED.value
        or gitlab_event_data.type == GitLabEventType.SEGMENT_OVERRIDE_DELETED.value
    ):
        feature_external_resources = generate_feature_external_resources(
            list(
                FeatureExternalResource.objects.filter(
                    feature_id=gitlab_event_data.feature_id
                )
            )
        )
        data = CallGitLabData(
            event_type=gitlab_event_data.type,
            gitlab_data=gitlab_event_data,
            feature_external_resources=feature_external_resources,
        )
        send_post_request(data)
        return

    if (
        gitlab_event_data.type
        == GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
    ):
        data = CallGitLabData(
            event_type=gitlab_event_data.type,
            gitlab_data=gitlab_event_data,
            feature_external_resources=[],
        )
        send_post_request(data)
        return

    feature = Feature.objects.get(id=gitlab_event_data.feature_id)
    feature_external_resources = generate_feature_external_resources(
        list(feature.external_resources.all())
    )
    data = CallGitLabData(
        event_type=gitlab_event_data.type,
        gitlab_data=gitlab_event_data,
        feature_external_resources=feature_external_resources,
    )

    if not feature_external_resources:
        logger.debug(
            "No GitLab external resources are associated with this feature id %d. "
            "Not calling webhooks.",
            gitlab_event_data.feature_id,
        )
        return

    send_post_request(data)
