from integrations.gitlab.client.api import (
    GitLabResourceKind,
    add_flagsmith_label_to_gitlab_resource,
    create_flagsmith_label,
    create_issue_note,
    create_merge_request_note,
    create_project_hook,
    delete_project_hook,
    fetch_gitlab_projects,
    remove_flagsmith_label_from_gitlab_resource,
    search_gitlab_issues,
    search_gitlab_merge_requests,
)
from integrations.gitlab.client.types import (
    GitLabIssue,
    GitLabMergeRequest,
    GitLabPage,
    GitLabProject,
    GitLabProjectHook,
)

__all__ = [
    "GitLabIssue",
    "GitLabMergeRequest",
    "GitLabPage",
    "GitLabProject",
    "GitLabProjectHook",
    "GitLabResourceKind",
    "add_flagsmith_label_to_gitlab_resource",
    "create_flagsmith_label",
    "create_issue_note",
    "create_merge_request_note",
    "create_project_hook",
    "delete_project_hook",
    "fetch_gitlab_projects",
    "remove_flagsmith_label_from_gitlab_resource",
    "search_gitlab_issues",
    "search_gitlab_merge_requests",
]
