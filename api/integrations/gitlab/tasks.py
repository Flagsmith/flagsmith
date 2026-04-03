import logging
import re
from typing import Any
from urllib.parse import urlparse

from task_processor.decorators import register_task_handler

from integrations.gitlab.client import post_comment_to_gitlab
from integrations.gitlab.constants import GitLabEventType
from integrations.gitlab.types import GitLabResourceEndpoint

logger = logging.getLogger(__name__)

UNLINKED_FEATURE_TEXT = "**The feature flag `%s` was unlinked from the issue/MR**"


def _parse_resource_url(resource_url: str) -> tuple[str, GitLabResourceEndpoint, int] | None:
    """Parse a GitLab resource URL into (project_path, resource_type, iid).

    Returns None if the URL format is not recognised.
    """
    parsed = urlparse(resource_url)
    path = parsed.path

    if "/-/merge_requests/" in path:
        resource_type: GitLabResourceEndpoint = "merge_requests"
        iid_match = re.search(r"/-/merge_requests/(\d+)", path)
    elif "/-/issues/" in path or "/-/work_items/" in path:
        resource_type = "issues"
        iid_match = re.search(r"/-/(?:issues|work_items)/(\d+)", path)
    else:
        return None

    if not iid_match:
        return None

    project_path_match = re.search(r"^/([^/]+(?:/[^/]+)*)/-/", path)
    if not project_path_match:
        return None

    return project_path_match.group(1), resource_type, int(iid_match.group(1))


@register_task_handler()
def post_gitlab_comment(
    project_id: int,
    feature_id: int,
    feature_name: str,
    event_type: str,
    feature_states: list[dict[str, Any]],
    url: str | None = None,
    segment_name: str | None = None,
) -> None:
    """Post a comment to linked GitLab resources when a feature changes.

    Fetches credentials from the DB — they are never passed through the
    task queue.
    """
    from features.feature_external_resources.models import (
        FeatureExternalResource,
        ResourceType,
    )
    from integrations.gitlab.models import GitLabConfiguration
    from integrations.vcs.comments import generate_body_comment

    try:
        gitlab_config = GitLabConfiguration.objects.get(
            project_id=project_id,
            deleted_at__isnull=True,
        )
    except GitLabConfiguration.DoesNotExist:
        logger.warning(
            "No GitLabConfiguration found for project_id=%s", project_id
        )
        return

    if not gitlab_config.gitlab_project_id:
        return

    body = generate_body_comment(
        name=feature_name,
        event_type=event_type,
        feature_id=feature_id,
        feature_states=feature_states,
        unlinked_feature_text=UNLINKED_FEATURE_TEXT,
        project_id=project_id,
        segment_name=segment_name,
    )

    # Determine which resource URLs to post to
    if event_type == GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
        resource_urls = [url] if url else []
    else:
        resources = FeatureExternalResource.objects.filter(
            feature_id=feature_id,
            type__in=[ResourceType.GITLAB_ISSUE, ResourceType.GITLAB_MR],
        )
        resource_urls = [r.url for r in resources]

    if not resource_urls:
        logger.debug(
            "No GitLab resources linked to feature_id=%s, skipping comment.",
            feature_id,
        )
        return

    for resource_url in resource_urls:
        parsed = _parse_resource_url(resource_url)
        if not parsed:
            logger.warning("Could not parse GitLab resource URL: %s", resource_url)
            continue

        _project_path, resource_type, resource_iid = parsed

        post_comment_to_gitlab(
            instance_url=gitlab_config.gitlab_instance_url,
            access_token=gitlab_config.access_token,
            gitlab_project_id=gitlab_config.gitlab_project_id,
            resource_type=resource_type,
            resource_iid=resource_iid,
            body=body,
        )
