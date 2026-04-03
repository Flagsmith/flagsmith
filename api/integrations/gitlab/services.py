import logging
from typing import Any

from django.db.models import Q

from features.models import Feature, FeatureState
from integrations.gitlab.constants import (
    GITLAB_TAG_COLOUR,
    GitLabEventType,
    GitLabTag,
    gitlab_tag_description,
)
from integrations.gitlab.mappers import map_feature_states_to_dicts
from integrations.gitlab.models import GitLabConfiguration
from projects.tags.models import Tag, TagType

logger = logging.getLogger(__name__)

_tag_by_event_type: dict[str, dict[str, GitLabTag | None]] = {
    "merge_request": {
        "close": GitLabTag.MR_CLOSED,
        "merge": GitLabTag.MR_MERGED,
        "open": GitLabTag.MR_OPEN,
        "reopen": GitLabTag.MR_OPEN,
        "update": None,
    },
    "issue": {
        "close": GitLabTag.ISSUE_CLOSED,
        "open": GitLabTag.ISSUE_OPEN,
        "reopen": GitLabTag.ISSUE_OPEN,
    },
}


def get_tag_for_event(
    event_type: str,
    action: str,
    metadata: dict[str, Any],
) -> GitLabTag | None:
    """Return the tag for a GitLab webhook event, or None if no tag change is needed."""
    if event_type == "merge_request" and action == "update":
        if metadata.get("draft", False):
            return GitLabTag.MR_DRAFT
        return None

    event_actions = _tag_by_event_type.get(event_type, {})
    return event_actions.get(action)


def tag_feature_per_gitlab_event(
    event_type: str,
    action: str,
    metadata: dict[str, Any],
    project_path: str,
) -> None:
    """Apply a tag to a feature based on a GitLab webhook event."""
    web_url = metadata.get("web_url", "")

    # GitLab webhooks send /-/issues/N but stored URL might be /-/work_items/N
    url_variants = [web_url]
    if "/-/issues/" in web_url:
        url_variants.append(web_url.replace("/-/issues/", "/-/work_items/"))
    elif "/-/work_items/" in web_url:
        url_variants.append(web_url.replace("/-/work_items/", "/-/issues/"))

    feature = None
    for url in url_variants:
        feature = Feature.objects.filter(
            Q(external_resources__type="GITLAB_MR")
            | Q(external_resources__type="GITLAB_ISSUE"),
            external_resources__url=url,
        ).first()
        if feature:
            break

    if not feature:
        return

    try:
        gitlab_config = GitLabConfiguration.objects.get(
            project=feature.project,
            project_name=project_path,
            deleted_at__isnull=True,
        )
    except GitLabConfiguration.DoesNotExist:
        return

    if not gitlab_config.tagging_enabled:
        return

    tag_enum = get_tag_for_event(event_type, action, metadata)
    if tag_enum is None:
        return

    gitlab_tag, _ = Tag.objects.get_or_create(
        color=GITLAB_TAG_COLOUR,
        description=gitlab_tag_description[tag_enum.value],
        label=tag_enum.value,
        project=feature.project,
        is_system_tag=True,
        type=TagType.GITLAB.value,
    )

    tag_label_pattern = "Issue" if event_type == "issue" else "MR"
    feature.tags.remove(
        *feature.tags.filter(
            Q(type=TagType.GITLAB.value) & Q(label__startswith=tag_label_pattern)
        )
    )
    feature.tags.add(gitlab_tag)
    feature.save()


def handle_gitlab_webhook_event(event_type: str, payload: dict[str, Any]) -> None:
    """Process a GitLab webhook payload and apply tags."""
    attrs = payload.get("object_attributes", {})
    action = attrs.get("action", "")
    project_path = payload.get("project", {}).get("path_with_namespace", "")

    metadata: dict[str, Any] = {"web_url": attrs.get("url", "")}
    if event_type == "merge_request":
        metadata["draft"] = attrs.get("work_in_progress", False)
        metadata["merged"] = attrs.get("state") == "merged"

    tag_feature_per_gitlab_event(event_type, action, metadata, project_path)


def dispatch_gitlab_comment(
    project_id: int,
    event_type: str,
    feature: Feature,
    feature_states: list[FeatureState] | None = None,
    url: str | None = None,
    segment_name: str | None = None,
) -> None:
    """Dispatch an async task to post a comment to linked GitLab resources.

    Does NOT pass credentials through the task queue — only the project_id.
    The task handler fetches the GitLabConfiguration from the DB.
    """
    from integrations.gitlab.tasks import post_gitlab_comment

    feature_states_data = (
        map_feature_states_to_dicts(feature_states, event_type)
        if feature_states
        else []
    )

    post_gitlab_comment.delay(
        kwargs={
            "project_id": project_id,
            "feature_id": feature.id,
            "feature_name": feature.name,
            "event_type": event_type,
            "feature_states": feature_states_data,
            "url": url if event_type == GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value else None,
            "segment_name": segment_name,
        },
    )
