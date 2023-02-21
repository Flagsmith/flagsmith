import typing

from django.db.models import Prefetch, Q
from flag_engine.features.models import FeatureStateModel
from flag_engine.identities.builders import (
    build_identity_dict,
    build_identity_model,
)
from flag_engine.identities.models import IdentityModel
from flag_engine.utils.collections import IdentityFeaturesList

from environments.dynamodb import DynamoIdentityWrapper
from environments.models import Environment
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureStateValue

from .tasks import sync_identity_document_features


class EdgeIdentity:
    dynamo_wrapper = DynamoIdentityWrapper()

    def __init__(self, engine_identity_model: IdentityModel):
        self._engine_identity_model = engine_identity_model

    @classmethod
    def from_identity_document(cls, identity_document: dict) -> "EdgeIdentity":
        return EdgeIdentity(build_identity_model(identity_document))

    @property
    def django_id(self) -> int:
        return self._engine_identity_model.django_id

    @property
    def environment_api_key(self) -> str:
        return self._engine_identity_model.environment_api_key

    @property
    def feature_overrides(self) -> IdentityFeaturesList:
        return self._engine_identity_model.identity_features

    @property
    def id(self) -> typing.Union[int, str]:
        return (
            self._engine_identity_model.django_id
            or self._engine_identity_model.identity_uuid
        )

    @property
    def identifier(self) -> str:
        return self._engine_identity_model.identifier

    @property
    def identity_uuid(self) -> str:
        return self._engine_identity_model.identity_uuid

    def add_feature_override(self, feature_state: FeatureStateModel) -> None:
        self._engine_identity_model.identity_features.append(feature_state)

    def get_all_feature_states(
        self,
    ) -> typing.Tuple[
        typing.List[typing.Union[FeatureState, FeatureStateModel]], typing.Set[str]
    ]:
        """
        Get all feature states for a flag engine identity model. The list returned by
        this function contains two distinct types: features.models.FeatureState &
        flag_engine.features.models.FeatureStateModel.

        :return: tuple of (list of feature states, set of feature names that were overridden
            for the identity specifically)
        """
        segment_ids = self.dynamo_wrapper.get_segment_ids(
            identity_model=self._engine_identity_model
        )
        django_environment = Environment.objects.get(api_key=self.environment_api_key)

        q = Q(identity__isnull=True) & (
            Q(feature_segment__segment__id__in=segment_ids)
            | Q(feature_segment__isnull=True)
        )
        environment_and_segment_feature_states = (
            django_environment.feature_states.select_related(
                "feature",
                "feature_segment",
                "feature_segment__segment",
                "feature_state_value",
            )
            .prefetch_related(
                Prefetch(
                    "multivariate_feature_state_values",
                    queryset=MultivariateFeatureStateValue.objects.select_related(
                        "multivariate_feature_option"
                    ),
                )
            )
            .filter(q)
        )

        feature_states = {}
        for feature_state in environment_and_segment_feature_states:
            feature_name = feature_state.feature.name
            if (
                feature_name not in feature_states
                or feature_state > feature_states[feature_name]
            ):
                feature_states[feature_name] = feature_state

        identity_feature_states = self.feature_overrides
        identity_feature_names = set()
        for identity_feature_state in identity_feature_states:
            feature_name = identity_feature_state.feature.name
            feature_states[feature_name] = identity_feature_state
            identity_feature_names.add(feature_name)

        return list(feature_states.values()), identity_feature_names

    def get_feature_state_by_feature_name_or_id(
        self, feature: typing.Union[str, int]
    ) -> typing.Optional[FeatureStateModel]:
        def match_feature_state(fs):
            if isinstance(feature, int):
                return fs.feature.id == feature
            return fs.feature.name == feature

        feature_state = next(
            filter(
                match_feature_state,
                self._engine_identity_model.identity_features,
            ),
            None,
        )

        return feature_state

    def get_feature_state_by_featurestate_uuid(
        self, featurestate_uuid: str
    ) -> typing.Optional[FeatureStateModel]:
        return next(
            filter(
                lambda fs: fs.featurestate_uuid == featurestate_uuid,
                self._engine_identity_model.identity_features,
            ),
            None,
        )

    def remove_feature_override(self, feature_state: FeatureStateModel) -> None:
        self._engine_identity_model.identity_features.remove(feature_state)

    def synchronise_features(self, valid_feature_names: typing.Collection[str]) -> None:
        identity_feature_names = {
            fs.feature.name for fs in self._engine_identity_model.identity_features
        }
        if not identity_feature_names.issubset(valid_feature_names):
            self._engine_identity_model.prune_features(list(valid_feature_names))
            sync_identity_document_features.delay(
                args=(str(self._engine_identity_model.identity_uuid),)
            )

    def to_document(self) -> dict:
        return build_identity_dict(self._engine_identity_model)
