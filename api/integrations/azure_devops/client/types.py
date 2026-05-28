from typing import TypedDict


class AdoProject(TypedDict):
    id: str
    name: str
    url: str


class AdoProjectsPage(TypedDict):
    results: list[AdoProject]
    continuation_token: str | None


class AdoRepository(TypedDict):
    id: str
    name: str
    default_branch: str


class AdoPullRequest(TypedDict):
    id: int
    title: str
    state: str
    is_draft: bool
    web_url: str
    repository_name: str


class AdoPullRequestsPage(TypedDict):
    results: list[AdoPullRequest]
    continuation_token: str | None


class AdoWorkItem(TypedDict):
    id: int
    title: str
    state: str
    work_item_type: str
    web_url: str


class AdoWorkItemsPage(TypedDict):
    results: list[AdoWorkItem]
    continuation_token: str | None
