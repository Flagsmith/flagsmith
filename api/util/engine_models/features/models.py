import typing
import uuid

from annotated_types import Ge, Le
from pydantic import UUID4, BaseModel, Field, model_validator
from pydantic_collections import BaseCollectionModel  # type: ignore[import-untyped]
from typing_extensions import Annotated

from util.engine_models.utils.exceptions import InvalidPercentageAllocation


class FeatureModel(BaseModel):
    id: int
    name: str
    type: str


class MultivariateFeatureOptionModel(BaseModel):
    value: typing.Any
    id: typing.Optional[int] = None
    key: typing.Optional[str] = None


class MultivariateFeatureStateValueModel(BaseModel):
    multivariate_feature_option: MultivariateFeatureOptionModel
    percentage_allocation: Annotated[float, Ge(0), Le(100)]
    id: typing.Optional[int] = None
    mv_fs_value_uuid: UUID4 = Field(default_factory=uuid.uuid4)


class FeatureSegmentModel(BaseModel):
    priority: typing.Optional[int] = None


class MultivariateFeatureStateValueList(
    BaseCollectionModel[MultivariateFeatureStateValueModel]  # type: ignore[misc]
):
    @staticmethod
    def _ensure_correct_percentage_allocations(
        value: typing.List[MultivariateFeatureStateValueModel],
    ) -> typing.List[MultivariateFeatureStateValueModel]:
        if (
            sum(
                multivariate_feature_state.percentage_allocation
                for multivariate_feature_state in value
            )
            > 100
        ):
            raise InvalidPercentageAllocation(
                "Total percentage allocation for feature must be less or equal to 100 percent"
            )
        return value

    percentage_allocations_model_validator = model_validator(mode="after")(
        _ensure_correct_percentage_allocations
    )

    def append(
        self,
        multivariate_feature_state_value: MultivariateFeatureStateValueModel,
    ) -> None:
        self._ensure_correct_percentage_allocations(
            [*self, multivariate_feature_state_value],
        )
        super().append(multivariate_feature_state_value)


class FeatureStateModel(BaseModel, validate_assignment=True):
    feature: FeatureModel
    enabled: bool
    django_id: typing.Optional[int] = None
    feature_segment: typing.Optional[FeatureSegmentModel] = None
    featurestate_uuid: UUID4 = Field(default_factory=uuid.uuid4)
    feature_state_value: typing.Any = None
    multivariate_feature_state_values: MultivariateFeatureStateValueList = Field(
        default_factory=MultivariateFeatureStateValueList
    )
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = Field(
        default=None,
        exclude_if=lambda value: not value,
    )

    def set_value(self, value: typing.Any) -> None:
        self.feature_state_value = value
