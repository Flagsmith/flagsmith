from typing import Any, TypedDict

JsonLogic = dict[str, Any]


class TranslationWarning(TypedDict):
    reason: str
    detail: str


class FlagdFlag(TypedDict, total=False):
    state: str
    variants: dict[str, Any]
    defaultVariant: str
    targeting: JsonLogic | None
    metadata: dict[str, Any]


class FlagdDocument(TypedDict, total=False):
    schema: str
    flags: dict[str, FlagdFlag]
    evaluators: dict[str, JsonLogic]
    metadata: dict[str, Any]
