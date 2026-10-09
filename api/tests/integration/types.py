from typing import Protocol

from features.dependencies.types import DependencyEdge
from features.future.types import UpdateFlagResponse


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
