from enum import Enum

GITLAB_TAG_COLOR = "#FC6D26"
GITLAB_WEBHOOK_TIMEOUT = 10


class GitLabTagLabel(Enum):
    ISSUE_OPEN = "Issue Open"
    ISSUE_CLOSED = "Issue Closed"
    MR_OPEN = "MR Open"
    MR_CLOSED = "MR Closed"
    MR_MERGED = "MR Merged"
    MR_DRAFT = "MR Draft"


GITLAB_TAG_DESCRIPTION_BY_LABEL: dict[GitLabTagLabel, str] = {
    GitLabTagLabel.ISSUE_OPEN: "Has a linked GitLab issue open",
    GitLabTagLabel.ISSUE_CLOSED: "Has a linked GitLab issue closed",
    GitLabTagLabel.MR_OPEN: "Has a linked GitLab merge request open",
    GitLabTagLabel.MR_CLOSED: "Has a linked GitLab merge request closed",
    GitLabTagLabel.MR_MERGED: "Has a linked GitLab merge request merged",
    GitLabTagLabel.MR_DRAFT: "Has a linked GitLab merge request draft",
}
