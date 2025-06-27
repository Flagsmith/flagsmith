from datetime import date
from typing import TYPE_CHECKING, Literal, NamedTuple, TypeAlias, TypedDict

if TYPE_CHECKING:
    from app_analytics.models import Resource

PeriodType = Literal[
    "current_billing_period",
    "previous_billing_period",
    "ninety_day_period",
]


class APIUsageCacheKey(NamedTuple):
    resource: "Resource"
    host: str
    environment_key: str
    labels: tuple[tuple[str, str], ...]


class FeatureEvaluationCacheKey(NamedTuple):
    feature_name: str
    environment_id: int
    labels: tuple[tuple["Label", str], ...]


class FeatureEvaluationKey(NamedTuple):
    feature_name: str
    labels: tuple[tuple["Label", str], ...]


class AnnotatedAPIUsageBucket(TypedDict):
    count: int
    created_at__date: date
    labels: "Labels"
    resource: "Resource"


class AnnotatedAPIUsageKey(NamedTuple):
    date: date
    labels: tuple[tuple["Label", str], ...]


# Optional labels Flagsmith stores for API usage and feature evaluation data.
Label = Literal[
    "client_application_name",
    "client_application_version",
    "user_agent",
]

Labels: TypeAlias = dict[Label, str]
