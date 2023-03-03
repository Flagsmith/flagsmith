from dataclasses import dataclass
from datetime import date


@dataclass
class UsageData:
    day: date
    flags: int = 0
    traits: int = 0
    identities: int = 0
    environment_document: int = 0


@dataclass
class FeatureEvaluationData:
    day: date
    count: int = 0
