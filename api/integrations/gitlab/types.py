from __future__ import annotations

from typing import Literal, TypedDict

from typing_extensions import NotRequired

GitLabResourceEndpoint = Literal["issues", "merge_requests"]


class GitLabProject(TypedDict):
    id: int
    name: str
    path_with_namespace: str


class GitLabResource(TypedDict):
    web_url: str
    id: int
    title: str
    iid: int
    state: str
    merged: bool
    draft: bool


class GitLabMember(TypedDict):
    username: str
    avatar_url: str
    name: str


class GitLabNote(TypedDict):
    id: int
    body: str


class GitLabLabel(TypedDict):
    id: int
    name: str


class GitLabResourceMetadata(TypedDict):
    title: str
    state: str


class PaginatedResponse(TypedDict):
    results: list[GitLabProject] | list[GitLabResource] | list[GitLabMember]
    next: NotRequired[int]
    previous: NotRequired[int]
    total_count: NotRequired[int]
