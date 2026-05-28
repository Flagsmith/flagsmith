from typing_extensions import TypedDict


class AzureDevOpsResourceMetadata(TypedDict, total=False):
    """Client-supplied snapshot persisted on ``FeatureExternalResource.metadata``
    when linking an Azure DevOps pull request or work item. Sent by the
    frontend as part of the link request; the backend stores it verbatim
    as a JSON string.

    Fields are typed for both PR and work-item resources; not every field
    applies to both — ``state`` is universal, ``is_draft`` is PR-only,
    ``work_item_type`` is work-item-only, ``title`` is universal.
    """

    title: str
    state: str
    work_item_type: str
    is_draft: bool
