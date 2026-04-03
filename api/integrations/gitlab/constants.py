from enum import Enum

GITLAB_API_CALLS_TIMEOUT = 10

GITLAB_FLAGSMITH_LABEL = "Flagsmith Flag"
GITLAB_FLAGSMITH_LABEL_DESCRIPTION = (
    "This GitLab Issue/MR is linked to a Flagsmith Feature Flag"
)
GITLAB_FLAGSMITH_LABEL_COLOUR = "6633FF"

GITLAB_TAG_COLOUR = "#838992"


class GitLabTag(Enum):
    MR_OPEN = "MR Open"
    MR_MERGED = "MR Merged"
    MR_CLOSED = "MR Closed"
    MR_DRAFT = "MR Draft"
    ISSUE_OPEN = "Issue Open"
    ISSUE_CLOSED = "Issue Closed"


class GitLabEventType(Enum):
    FLAG_UPDATED = "FLAG_UPDATED"
    FLAG_DELETED = "FLAG_DELETED"
    FEATURE_EXTERNAL_RESOURCE_ADDED = "FEATURE_EXTERNAL_RESOURCE_ADDED"
    FEATURE_EXTERNAL_RESOURCE_REMOVED = "FEATURE_EXTERNAL_RESOURCE_REMOVED"
    SEGMENT_OVERRIDE_DELETED = "SEGMENT_OVERRIDE_DELETED"


gitlab_tag_description: dict[str, str] = {
    GitLabTag.MR_OPEN.value: "This feature has a linked MR open",
    GitLabTag.MR_MERGED.value: "This feature has a linked MR merged",
    GitLabTag.MR_CLOSED.value: "This feature has a linked MR closed",
    GitLabTag.MR_DRAFT.value: "This feature has a linked MR draft",
    GitLabTag.ISSUE_OPEN.value: "This feature has a linked issue open",
    GitLabTag.ISSUE_CLOSED.value: "This feature has a linked issue closed",
}
