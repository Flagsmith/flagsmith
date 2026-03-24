from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GitLabData:
    gitlab_instance_url: str
    access_token: str
    feature_id: int
    feature_name: str
    type: str
    feature_states: list[dict[str, Any]] = field(default_factory=list)
    url: str | None = None
    project_id: int | None = None
    segment_name: str | None = None

    @classmethod
    def from_dict(cls, data_dict: dict[str, Any]) -> "GitLabData":
        return cls(**data_dict)


@dataclass
class CallGitLabData:
    event_type: str
    gitlab_data: GitLabData
    feature_external_resources: list[dict[str, Any]]


@dataclass
class PaginatedQueryParams:
    page: int = field(default=1, kw_only=True)
    page_size: int = field(default=100, kw_only=True)

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("Page must be greater or equal than 1")
        if self.page_size < 1 or self.page_size > 100:
            raise ValueError("Page size must be an integer between 1 and 100")


@dataclass
class ProjectQueryParams(PaginatedQueryParams):
    gitlab_project_id: int = 0
    project_name: str = ""


@dataclass
class IssueQueryParams(ProjectQueryParams):
    search_text: Optional[str] = None
    state: Optional[str] = "opened"
    author: Optional[str] = None
    assignee: Optional[str] = None
