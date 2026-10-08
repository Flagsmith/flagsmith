from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

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
class FlagChangeSet:
    author: AuthorData
    enabled: bool
    feature_state_value: str
    type_: FeatureValueType

    segment_id: int | None = None
    segment_priority: int | None = None
    multivariate_values: list[MultivariateValueChangeSet] | None = None


@dataclass
class MultivariateValueChangeSet:
    multivariate_feature_option_id: int
    percentage_allocation: float
