from pydantic import TypeAdapter, ValidationError

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from integrations.azure_devops.constants import AzureDevOpsTagLabel
from integrations.azure_devops.types import AzureDevOpsResourceMetadata

_resource_metadata_adapter: TypeAdapter[AzureDevOpsResourceMetadata] = TypeAdapter(
    AzureDevOpsResourceMetadata,
)


_PR_OPEN_STATES = {"active"}
_PR_MERGED_STATES = {"completed"}
_PR_ABANDONED_STATES = {"abandoned"}


_WORK_ITEM_OPEN_STATES = {
    "new",
    "active",
    "to do",
    "in progress",
    "doing",
    "approved",
    "committed",
    "open",
    "resolved",
}
_WORK_ITEM_CLOSED_STATES = {"closed", "done", "removed"}


def map_pr_state_to_tag_label(
    state: str | None,
    *,
    is_draft: bool,
) -> AzureDevOpsTagLabel | None:
    """Map an Azure DevOps pull-request state (+ draft flag) to a Flagsmith
    tag label, or ``None`` if the state is unknown.
    """
    if not state:
        return None
    normalised = state.lower()
    if normalised in _PR_ABANDONED_STATES:
        return AzureDevOpsTagLabel.PR_ABANDONED
    if normalised in _PR_MERGED_STATES:
        return AzureDevOpsTagLabel.PR_MERGED
    if normalised in _PR_OPEN_STATES:
        return AzureDevOpsTagLabel.PR_DRAFT if is_draft else AzureDevOpsTagLabel.PR_OPEN
    return None


def map_work_item_state_to_tag_label(
    state: str | None,
) -> AzureDevOpsTagLabel | None:
    """Map an Azure DevOps work-item state to a Flagsmith tag label, or
    ``None`` if the state is unknown. Covers the common states across
    Agile, Scrum, and Basic process templates.
    """
    if not state:
        return None
    normalised = state.lower()
    if normalised in _WORK_ITEM_CLOSED_STATES:
        return AzureDevOpsTagLabel.WORK_ITEM_CLOSED
    if normalised in _WORK_ITEM_OPEN_STATES:
        return AzureDevOpsTagLabel.WORK_ITEM_OPEN
    return None


def map_resource_to_tag_label(
    resource: FeatureExternalResource,
) -> AzureDevOpsTagLabel | None:
    """Derive the Azure DevOps tag label for ``resource.feature`` from the
    JSON metadata snapshot the client supplied at link time. Returns
    ``None`` if the metadata is missing, malformed, or the state isn't
    recognised.
    """
    try:
        metadata = _resource_metadata_adapter.validate_json(resource.metadata or "")
    except ValidationError:
        return None
    state = metadata.get("state")
    if resource.type == ResourceType.AZURE_DEVOPS_PULL_REQUEST.value:
        return map_pr_state_to_tag_label(
            state,
            is_draft=bool(metadata.get("is_draft")),
        )
    if resource.type == ResourceType.AZURE_DEVOPS_WORK_ITEM.value:
        return map_work_item_state_to_tag_label(state)
    return None
