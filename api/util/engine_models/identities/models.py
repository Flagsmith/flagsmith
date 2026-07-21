import datetime
import typing
import uuid

from pydantic import UUID4, BaseModel, Field, computed_field, model_validator
from pydantic_collections import BaseCollectionModel  # type: ignore[import-untyped]

from util.engine_models.features.models import FeatureStateModel
from util.engine_models.identities.traits.models import TraitModel
from util.engine_models.utils.datetime import utcnow_with_tz
from util.engine_models.utils.exceptions import DuplicateFeatureState


class IdentityFeaturesList(BaseCollectionModel[FeatureStateModel]):  # type: ignore[misc]
    @staticmethod
    def _ensure_unique_feature_ids(
        value: typing.Sequence[FeatureStateModel],
    ) -> None:
        for i, feature_state in enumerate(value, start=1):
            if feature_state.feature.id in [
                feature_state.feature.id for feature_state in value[i:]
            ]:
                raise DuplicateFeatureState(
                    f"Feature state for feature id={feature_state.feature.id} already exists"
                )

    @model_validator(mode="after")
    def ensure_unique_feature_ids(self) -> "IdentityFeaturesList":
        self._ensure_unique_feature_ids(self.root)
        return self

    def append(self, feature_state: "FeatureStateModel") -> None:
        self._ensure_unique_feature_ids([*self, feature_state])
        super().append(feature_state)


class IdentityModel(BaseModel):
    identifier: str
    environment_api_key: str
    created_date: datetime.datetime = Field(default_factory=utcnow_with_tz)
    identity_features: IdentityFeaturesList = Field(
        default_factory=IdentityFeaturesList
    )
    identity_traits: typing.List[TraitModel] = Field(default_factory=list)
    identity_uuid: UUID4 = Field(default_factory=uuid.uuid4)
    django_id: typing.Optional[int] = None

    dashboard_alias: typing.Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def composite_key(self) -> str:
        return self.generate_composite_key(self.environment_api_key, self.identifier)

    @staticmethod
    def generate_composite_key(env_key: str, identifier: str) -> str:
        return f"{env_key}_{identifier}"

    def get_hash_key(self, use_identity_composite_key_for_hashing: bool) -> str:
        return (
            self.composite_key
            if use_identity_composite_key_for_hashing
            else self.identifier
        )

    def update_traits(
        self, traits: typing.List[TraitModel]
    ) -> typing.Tuple[typing.List[TraitModel], bool]:
        existing_traits = {trait.trait_key: trait for trait in self.identity_traits}
        traits_changed = False

        for trait in traits:
            existing_trait = existing_traits.get(trait.trait_key)

            if trait.trait_value is None and existing_trait:
                existing_traits.pop(trait.trait_key)
                traits_changed = True

            elif getattr(existing_trait, "trait_value", None) != trait.trait_value:
                existing_traits[trait.trait_key] = trait
                traits_changed = True

        self.identity_traits = list(existing_traits.values())
        return self.identity_traits, traits_changed

    def prune_features(self, valid_feature_names: typing.List[str]) -> None:
        self.identity_features = IdentityFeaturesList(
            [
                fs
                for fs in self.identity_features
                if fs.feature.name in valid_feature_names
            ]
        )
