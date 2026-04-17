from typing import Generic, TypedDict, TypeVar

T = TypeVar("T")


class GitLabProject(TypedDict):
    id: int
    name: str
    path_with_namespace: str


class GitLabIssue(TypedDict):
    web_url: str
    id: int
    title: str
    iid: int
    state: str


class GitLabMergeRequest(TypedDict):
    web_url: str
    id: int
    title: str
    iid: int
    state: str
    merged: bool
    draft: bool


class GitLabPage(TypedDict, Generic[T]):
    results: list[T]
    current_page: int
    total_pages: int
    total_count: int
