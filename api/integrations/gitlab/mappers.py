from pydantic import TypeAdapter, ValidationError

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from integrations.gitlab.constants import GitLabTagLabel
from integrations.gitlab.types import GitLabResourceMetadata, GitLabWebhookPayload

_resource_metadata_adapter: TypeAdapter[GitLabResourceMetadata] = TypeAdapter(
    GitLabResourceMetadata,
)


def map_issue_state_to_tag_label(state: str | None) -> GitLabTagLabel | None:
    if state in {"opened", "reopened", "open"}:
        return GitLabTagLabel.ISSUE_OPEN
    if state == "closed":
        return GitLabTagLabel.ISSUE_CLOSED
    return None


def map_merge_request_state_to_tag_label(
    state: str | None,
    action: str | None,
    is_draft: bool,
) -> GitLabTagLabel | None:
    if action == "merge" or state == "merged":
        return GitLabTagLabel.MR_MERGED
    if state == "closed":
        return GitLabTagLabel.MR_CLOSED
    if state in {"opened", "reopened", "open"}:
        return GitLabTagLabel.MR_DRAFT if is_draft else GitLabTagLabel.MR_OPEN
    return None


def map_gitlab_resource_to_tag_label(
    resource: FeatureExternalResource,
) -> GitLabTagLabel | None:
    """Derive the GitLab tag label for ``resource.feature`` from the JSON
    metadata snapshot the client supplied at link time.
    """
    try:
        metadata = _resource_metadata_adapter.validate_json(resource.metadata or "")
    except ValidationError:
        return None
    state = metadata.get("state")
    if resource.type == ResourceType.GITLAB_ISSUE.value:
        return map_issue_state_to_tag_label(state)
    if resource.type == ResourceType.GITLAB_MR.value:
        return map_merge_request_state_to_tag_label(
            state,
            action=None,
            is_draft=bool(metadata.get("draft")),
        )
    return None


def map_gitlab_webhook_payload_to_tag_label(
    payload: GitLabWebhookPayload,
) -> GitLabTagLabel | None:
    attrs = payload.get("object_attributes")
    if not attrs:
        return None
    state = attrs.get("state")
    object_kind = payload.get("object_kind")
    if object_kind == "issue":
        return map_issue_state_to_tag_label(state)
    if object_kind == "merge_request":
        return map_merge_request_state_to_tag_label(
            state,
            action=attrs.get("action"),
            is_draft=bool(attrs.get("draft") or attrs.get("work_in_progress")),
        )
    return None
