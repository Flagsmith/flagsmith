from dataclasses import dataclass
from datetime import date

from app_analytics.types import Labels


@dataclass
class UsageData:
    day: date
    flags: int = 0
    traits: int = 0
    identities: int = 0
    environment_document: int = 0
    labels: Labels | None = None


@dataclass
class FeatureEvaluationData:
    day: date
    count: int = 0
    labels: Labels | None = None
