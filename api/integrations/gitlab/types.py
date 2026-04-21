from typing import TypedDict


class GitLabResourceMetadata(TypedDict, total=False):
    """Client-supplied snapshot persisted on ``FeatureExternalResource.metadata``
    when linking a GitLab issue or MR. Sent by the frontend as part of the
    link request; the backend stores it verbatim as a JSON string.
    """

    title: str
    state: str
    draft: bool


class GitLabWebhookObjectAttributes(TypedDict, total=False):
    url: str
    state: str
    action: str
    draft: bool
    work_in_progress: bool


class GitLabWebhookPayload(TypedDict, total=False):
    object_kind: str
    object_attributes: GitLabWebhookObjectAttributes
