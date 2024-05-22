import copy
import typing
from contextlib import suppress

from django.db.models import Prefetch, Q
from flag_engine.features.models import FeatureStateModel
from flag_engine.identities.models import IdentityFeaturesList, IdentityModel

from api_keys.models import MasterAPIKey
from edge_api.identities.tasks import (
    generate_audit_log_records,
    sync_identity_document_features,
    update_flagsmith_environments_v2_identity_overrides,
)
from edge_api.identities.types import IdentityChangeset
from edge_api.identities.utils import generate_change_dict
from environments.dynamodb import DynamoIdentityWrapper
from environments.models import Environment
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from features.versioning.versioning_service import get_environment_flags_dict
from users.models import FFAdminUser
from util.mappers import map_engine_identity_to_identity_document


class EdgeIdentity:
    dynamo_wrapper = DynamoIdentityWrapper()

    def __init__(self, engine_identity_model: IdentityModel):
        self._engine_identity_model = engine_identity_model
        self._reset_initial_state()

    @classmethod
    def from_identity_document(cls, identity_document: dict) -> "EdgeIdentity":
        return EdgeIdentity(IdentityModel.model_validate(identity_document))

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
        return self._engine_identity_model.django_id or str(
            self._engine_identity_model.identity_uuid
        )

    @property
    def identifier(self) -> str:
        return self._engine_identity_model.identifier

    @property
    def identity_uuid(self) -> str:
        return str(self._engine_identity_model.identity_uuid)

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

        # since identity overrides are included in the document retrieved from dynamo,
        # we only want to retrieve the environment default and (relevant) segment overrides
        # from the ORM.
        additional_filters = Q(identity__isnull=True) & (
            Q(feature_segment__segment__id__in=segment_ids)
            | Q(feature_segment__isnull=True)
        )

        feature_states: dict[str, FeatureState | FeatureStateModel] = (
            get_environment_flags_dict(
                environment=django_environment,
                additional_filters=additional_filters,
                additional_select_related_args=[
                    "feature",
                    "feature_segment",
                    "feature_segment__segment",
                    "feature_state_value",
                ],
                additional_prefetch_related_args=[
                    Prefetch(
                        "multivariate_feature_state_values",
                        queryset=MultivariateFeatureStateValue.objects.select_related(
                            "multivariate_feature_option"
                        ),
                    )
                ],
                # since we only want to retrieve the highest priority feature state,
                # we key off the feature name instead of the default
                # (feature_id, segment_id, identity_id). This will give us only e.g.
                # the highest priority matching segment override for a given feature.
                key_function=lambda fs: fs.feature.name,
            )
        )

        # Since the identity overrides are the highest priority, we can now iterate
        # over the dictionary and replace any feature states with those that have
        # an identity override, stored against the identity in dynamo.
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
                lambda fs: str(fs.featurestate_uuid) == featurestate_uuid,
                self._engine_identity_model.identity_features,
            ),
            None,
        )

    def get_hash_key(self, use_identity_composite_key_for_hashing: bool) -> str:
        return self._engine_identity_model.get_hash_key(
            use_identity_composite_key_for_hashing
        )

    def remove_feature_override(self, feature_state: FeatureStateModel) -> None:
        with suppress(ValueError):  # ignore if feature state didn't exist
            self._engine_identity_model.identity_features.remove(feature_state)

    def save(self, user: FFAdminUser = None, master_api_key: MasterAPIKey = None):
        self.dynamo_wrapper.put_item(self.to_document())
        changes = self._get_changes()
        if changes["feature_overrides"]:
            # TODO: would this be simpler if we put a wrapper around FeatureStateModel instead?
            generate_audit_log_records.delay(
                kwargs={
                    "environment_api_key": self.environment_api_key,
                    "identifier": self.identifier,
                    "user_id": getattr(user, "id", None),
                    "changes": changes,
                    "identity_uuid": str(self.identity_uuid),
                    "master_api_key_id": getattr(master_api_key, "id", None),
                }
            )
            update_flagsmith_environments_v2_identity_overrides.delay(
                kwargs={
                    "environment_api_key": self.environment_api_key,
                    "changes": changes,
                    "identity_uuid": str(self.identity_uuid),
                    "identifier": self.identifier,
                }
            )
        self._reset_initial_state()

    def synchronise_features(self, valid_feature_names: typing.Collection[str]) -> None:
        identity_feature_names = {
            fs.feature.name for fs in self._engine_identity_model.identity_features
        }
        if not identity_feature_names.issubset(valid_feature_names):
            self._engine_identity_model.prune_features(list(valid_feature_names))
            sync_identity_document_features.delay(args=(str(self.identity_uuid),))

    def to_document(self) -> dict:
        return map_engine_identity_to_identity_document(self._engine_identity_model)

    def _get_changes(self) -> IdentityChangeset:
        previous_instance = self._initial_state
        changes = {}
        feature_changes = changes.setdefault("feature_overrides", {})
        previous_feature_overrides = {
            fs.featurestate_uuid: fs for fs in previous_instance.feature_overrides
        }
        current_feature_overrides = {
            fs.featurestate_uuid: fs for fs in self.feature_overrides
        }

        for uuid_, previous_fs in previous_feature_overrides.items():
            current_matching_fs = current_feature_overrides.get(uuid_)
            if current_matching_fs is None:
                feature_changes[previous_fs.feature.name] = generate_change_dict(
                    change_type="-",
                    identity_id=self.id,
                    old=previous_fs,
                )
            elif (
                current_matching_fs.enabled != previous_fs.enabled
                or current_matching_fs.get_value(self.id)
                != previous_fs.get_value(self.id)
            ):
                feature_changes[previous_fs.feature.name] = generate_change_dict(
                    change_type="~",
                    identity_id=self.id,
                    new=current_matching_fs,
                    old=previous_fs,
                )

        for uuid_, previous_fs in current_feature_overrides.items():
            if uuid_ not in previous_feature_overrides:
                feature_changes[previous_fs.feature.name] = generate_change_dict(
                    change_type="+",
                    identity_id=self.id,
                    new=previous_fs,
                )

        return changes

    def _reset_initial_state(self):
        self._initial_state = copy.deepcopy(self)

    def clone_flag_states_from(self, source_identity: "EdgeIdentity") -> None:
        """
        Clone the feature states from the source identity to the target identity.
        """
        # Delete identity_target's feature states
        for feature_state in list(self.feature_overrides):
            self.remove_feature_override(feature_state=feature_state)

        # Clone identity_source's feature states to identity_target
        for feature_in_source in source_identity.feature_overrides:
            feature_state_target = FeatureStateModel(
                feature=feature_in_source.feature,
                feature_state_value=feature_in_source.feature_state_value,
                enabled=feature_in_source.enabled,
                multivariate_feature_state_values=feature_in_source.multivariate_feature_state_values,
            )
            self.add_feature_override(feature_state_target)
