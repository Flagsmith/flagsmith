from datetime import datetime
from typing import Protocol

from features.dependencies.types import DependencyEdge
from features.future.types import UpdateFlagResponse
from features.workflows.core.models import ChangeRequest


class GetFeatureFixture(Protocol):
    def __call__(
        self,
        environment_api_key: str,
        feature_id: int,
    ) -> UpdateFlagResponse: ...


class AddFeaturePrerequisiteFixture(Protocol):
    def __call__(
        self,
        environment_api_key: str,
        feature_id: int,
        prerequisite_feature_id: int,
    ) -> DependencyEdge: ...


class CreateChangeRequestFixture(Protocol):
    def __call__(
        self,
        feature_id: int,
        title: str,
        live_from: datetime | None = None,
    ) -> ChangeRequest: ...
