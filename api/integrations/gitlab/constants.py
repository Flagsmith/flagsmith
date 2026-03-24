from enum import Enum

GITLAB_API_VERSION = "v4"
GITLAB_API_CALLS_TIMEOUT = 10

LINK_FEATURE_TITLE = """**Flagsmith feature linked:** `%s`
Default Values:\n"""
FEATURE_TABLE_HEADER = """| Environment | Enabled | Value | Last Updated (UTC) |
| :--- | :----- | :------ | :------ |\n"""
FEATURE_TABLE_ROW = "| [%s](%s) | %s | %s | %s |\n"
LINK_SEGMENT_TITLE = "Segment `%s` values:\n"
UNLINKED_FEATURE_TEXT = "**The feature flag `%s` was unlinked from the issue/MR**"
UPDATED_FEATURE_TEXT = "**Flagsmith Feature `%s` has been updated:**\n"
DELETED_FEATURE_TEXT = "**The Feature Flag `%s` was deleted**"
DELETED_SEGMENT_OVERRIDE_TEXT = (
    "**The Segment Override `%s` for Feature Flag `%s` was deleted**"
)
FEATURE_ENVIRONMENT_URL = "%s/project/%s/environment/%s/features?feature=%s&tab=%s"

CLEANUP_ISSUE_TITLE = "Remove stale feature flag: %s"
CLEANUP_ISSUE_BODY = """\
We need to clean up feature flag usage in the code.
Our goal is to delete references of the "%s" feature.
We need to delete the feature flag check so that the code path \
is no longer guarded by the feature flag.
These are the occurrences of this feature flag in this repository:
%s"""

GITLAB_TAG_COLOR = "#838992"
GITLAB_FLAGSMITH_LABEL = "Flagsmith Flag"
GITLAB_FLAGSMITH_LABEL_DESCRIPTION = (
    "This GitLab Issue/MR is linked to a Flagsmith Feature Flag"
)
GITLAB_FLAGSMITH_LABEL_COLOR = "6633FF"


class GitLabEventType(Enum):
    FLAG_UPDATED = "FLAG_UPDATED"
    FLAG_DELETED = "FLAG_DELETED"
    FEATURE_EXTERNAL_RESOURCE_ADDED = "FEATURE_EXTERNAL_RESOURCE_ADDED"
    FEATURE_EXTERNAL_RESOURCE_REMOVED = "FEATURE_EXTERNAL_RESOURCE_REMOVED"
    SEGMENT_OVERRIDE_DELETED = "SEGMENT_OVERRIDE_DELETED"


class GitLabTag(Enum):
    MR_OPEN = "MR Open"
    MR_MERGED = "MR Merged"
    MR_CLOSED = "MR Closed"
    MR_DRAFT = "MR Draft"
    ISSUE_OPEN = "Issue Open"
    ISSUE_CLOSED = "Issue Closed"


gitlab_tag_description = {
    GitLabTag.MR_OPEN.value: "This feature has a linked MR open",
    GitLabTag.MR_MERGED.value: "This feature has a linked MR merged",
    GitLabTag.MR_CLOSED.value: "This feature has a linked MR closed",
    GitLabTag.MR_DRAFT.value: "This feature has a linked MR draft",
    GitLabTag.ISSUE_OPEN.value: "This feature has a linked issue open",
    GitLabTag.ISSUE_CLOSED.value: "This feature has a linked issue closed",
}
