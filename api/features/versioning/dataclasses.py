from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeAlias

from pydantic import BaseModel, computed_field

from core.dataclasses import AuthorData
from features.feature_states.models import FeatureValueType


class Conflict(BaseModel):
    segment_id: int | None = None
    original_cr_id: int | None = None
    published_at: datetime | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_environment_default(self) -> bool:
        return self.segment_id is None


@dataclass
class FeatureValue:
    type_: FeatureValueType
    value: str


@dataclass
class FlagChangeSetOptionA:
    author: AuthorData
    enabled: bool | None = None
    value: FeatureValue | None = None

    segment_id: int | None = None
    segment_priority: int | None = None
    multivariate_values: list[MultivariateValueChangeSet] | None = None
    environment_multivariate_values: (
        list[EnvironmentMultivariateValueChangeSet] | None
    ) = None


@dataclass
class MultivariateValueChangeSet:
    multivariate_feature_option_id: int
    percentage_allocation: float


@dataclass
class NewMultivariateOptionChangeSet:
    percentage_allocation: float
    value: FeatureValue


@dataclass
class MultivariateOptionUpdateChangeSet:
    multivariate_feature_option_id: int
    percentage_allocation: float
    value: FeatureValue | None = None


EnvironmentMultivariateValueChangeSet: TypeAlias = (
    NewMultivariateOptionChangeSet | MultivariateOptionUpdateChangeSet
)


@dataclass
class SegmentOverrideChangeSet:
    segment_id: int
    enabled: bool | None = None
    value: FeatureValue | None = None
    priority: int | None = None
    multivariate_values: list[MultivariateValueChangeSet] | None = None


@dataclass
class EnvironmentDefaultChangeSet:
    enabled: bool | None = None
    value: FeatureValue | None = None
    multivariate_values: list[EnvironmentMultivariateValueChangeSet] | None = None


@dataclass
class FlagChangeSetOptionB:
    author: AuthorData
    environment_default: EnvironmentDefaultChangeSet | None = None

    segment_overrides: list[SegmentOverrideChangeSet] = field(default_factory=list)
