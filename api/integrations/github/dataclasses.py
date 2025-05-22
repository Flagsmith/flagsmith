from dataclasses import dataclass, field
from typing import Any, Optional


# Base Dataclasses
@dataclass
class GithubData:
    installation_id: str
    feature_id: int
    feature_name: str
    type: str
    feature_states: list[dict[str, Any]] | None = None
    url: str | None = None
    project_id: int | None = None
    segment_name: str | None = None

    @classmethod
    def from_dict(cls, data_dict: dict[str, Any]) -> "GithubData":
        return cls(**data_dict)


@dataclass
class CallGithubData:
    event_type: str
    github_data: GithubData
    feature_external_resources: list[dict[str, Any]]


# Dataclasses for external calls to GitHub API
@dataclass
class PaginatedQueryParams:
    page: int = field(default=1, kw_only=True)
    page_size: int = field(default=100, kw_only=True)

    def __post_init__(self):  # type: ignore[no-untyped-def]
        if self.page < 1:
            raise ValueError("Page must be greater or equal than 1")
        if self.page_size < 1 or self.page_size > 100:
            raise ValueError("Page size must be an integer between 1 and 100")


@dataclass
class RepoQueryParams(PaginatedQueryParams):
    repo_owner: str
    repo_name: str


@dataclass
class IssueQueryParams(RepoQueryParams):
    search_text: Optional[str] = None
    state: Optional[str] = "open"
    author: Optional[str] = None
    assignee: Optional[str] = None
    search_in_body: Optional[bool] = True
    search_in_comments: Optional[bool] = False
