from typing import TypedDict


class AdoProject(TypedDict):
    id: str
    name: str
    url: str


class AdoProjectsPage(TypedDict):
    results: list[AdoProject]
    continuation_token: str | None
