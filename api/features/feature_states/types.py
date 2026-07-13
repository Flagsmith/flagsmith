from collections.abc import Sequence
from typing import Never, NotRequired, TypeAlias, TypedDict

from features.feature_states.models import FeatureValueType


class FeatureValuePayload(TypedDict):
    type: FeatureValueType
    value: str


class FeatureNamePayload(TypedDict):
    name: str


class FeatureIdPayload(TypedDict):
    id: int


FeatureIdentifierPayload: TypeAlias = FeatureNamePayload | FeatureIdPayload


class SegmentReferencePayload(TypedDict):
    id: int
    priority: NotRequired[int | None]


class SegmentIdentifierPayload(TypedDict):
    id: int


class BaseMultivariateValuePayload(TypedDict):
    percentage_allocation: float


class NewMultivariateOptionPayload(BaseMultivariateValuePayload):
    multivariate_feature_option: NotRequired[Never]
    value: FeatureValuePayload


class MultivariateOptionUpdatePayload(BaseMultivariateValuePayload):
    multivariate_feature_option: int
    value: NotRequired[FeatureValuePayload]


EnvironmentMultivariateValuePayload: TypeAlias = (
    NewMultivariateOptionPayload | MultivariateOptionUpdatePayload
)


class SegmentOverrideMultivariateValuePayload(BaseMultivariateValuePayload):
    multivariate_feature_option: int


class UpdateFlagV1Payload(TypedDict):
    feature: FeatureIdentifierPayload
    segment: NotRequired[SegmentReferencePayload]
    enabled: NotRequired[bool]
    value: NotRequired[FeatureValuePayload]
    multivariate_feature_state_values: NotRequired[
        Sequence[EnvironmentMultivariateValuePayload]
    ]


class EnvironmentDefaultPayload(TypedDict):
    enabled: NotRequired[bool]
    value: NotRequired[FeatureValuePayload]
    multivariate_feature_state_values: NotRequired[
        Sequence[EnvironmentMultivariateValuePayload]
    ]


class SegmentOverridePayload(TypedDict):
    segment_id: int
    priority: NotRequired[int | None]
    enabled: NotRequired[bool]
    value: NotRequired[FeatureValuePayload]
    multivariate_feature_state_values: NotRequired[
        list[SegmentOverrideMultivariateValuePayload]
    ]


class UpdateFlagV2Payload(TypedDict):
    feature: FeatureIdentifierPayload
    environment_default: NotRequired[EnvironmentDefaultPayload]
    segment_overrides: NotRequired[list[SegmentOverridePayload]]


class DeleteSegmentOverridePayload(TypedDict):
    feature: FeatureIdentifierPayload
    segment: SegmentIdentifierPayload
