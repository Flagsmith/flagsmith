from typing import TypedDict


class GrafanaAnnotation(TypedDict):
    tags: list[str]
    text: str
    time: int
    timeEnd: int
