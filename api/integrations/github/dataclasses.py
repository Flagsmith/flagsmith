import typing
from dataclasses import dataclass
from typing import Optional


@dataclass
class GithubData:
    installation_id: str
    feature_id: int
    feature_name: str
    type: str
    feature_states: typing.List[dict[str, typing.Any]] | None = None
    url: str | None = None
    project_id: int | None = None
    segment_name: str | None = None

    @classmethod
    def from_dict(cls, data_dict: dict) -> "GithubData":
        return cls(**data_dict)


@dataclass
class CallGithubData:
    event_type: str
    github_data: GithubData
    feature_external_resources: list[dict[str, typing.Any]]


@dataclass
class RepoQueryParams:
    repo_owner: str
    repo_name: str
    search_text: Optional[str] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 100
    state: Optional[str] = "open"
    author: Optional[str] = None
    assignee: Optional[str] = None
    search_in_body: Optional[bool] = True
    search_in_comments: Optional[bool] = False

    @classmethod
    def from_dict(cls, data_dict: dict) -> "RepoQueryParams":
        return cls(**data_dict)
