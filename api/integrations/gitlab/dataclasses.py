from dataclasses import dataclass, field


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
    search_text: str | None = None
    state: str | None = "opened"
    author: str | None = None
    assignee: str | None = None
