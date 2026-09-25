import copy
import typing
from contextlib import suppress
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from api_keys.user import APIKeyUser
from edge_api.identities.tasks import (
    generate_audit_log_records,
    sync_identity_document_features,
    update_flagsmith_environments_v2_identity_overrides,
)
from edge_api.identities.types import IdentityChangeset
from edge_api.identities.utils import generate_change_dict
from environments.dynamodb import DynamoIdentityWrapper
from environments.models import Environment
from evaluation.services import get_edge_identity_override_value
from users.models import FFAdminUser
from util.engine_models.features.models import FeatureStateModel
from util.engine_models.identities.models import IdentityFeaturesList, IdentityModel
from util.mappers import map_engine_identity_to_identity_document


class EdgeIdentity:
    dynamo_wrapper = DynamoIdentityWrapper()

    def __init__(self, engine_identity_model: IdentityModel):
        self.engine_identity_model = engine_identity_model
        self._reset_initial_state()  # type: ignore[no-untyped-call]

    @classmethod
    def from_identity_document(cls, identity_document: dict) -> "EdgeIdentity":  # type: ignore[type-arg]
        return EdgeIdentity(IdentityModel.model_validate(identity_document))

    @property
    def environment_api_key(self) -> str:
        return self.engine_identity_model.environment_api_key

    @property
    def feature_overrides(self) -> IdentityFeaturesList:
        return self.engine_identity_model.identity_features

    @property
    def id(self) -> typing.Union[int, str]:
        return self.engine_identity_model.django_id or str(
            self.engine_identity_model.identity_uuid
        )

    @property
    def identifier(self) -> str:
        return self.engine_identity_model.identifier

    @property
    def identity_uuid(self) -> str:
        return str(self.engine_identity_model.identity_uuid)

    @property
    def environment(self) -> Environment:
        environment: Environment = Environment.objects.get(
            api_key=self.environment_api_key
        )
        return environment

    @property
    def dashboard_alias(self) -> str | None:
        return self.engine_identity_model.dashboard_alias

    @dashboard_alias.setter
    def dashboard_alias(self, dashboard_alias: str) -> None:
        self.engine_identity_model.dashboard_alias = dashboard_alias

    def add_feature_override(self, feature_state: FeatureStateModel) -> None:
        self.engine_identity_model.identity_features.append(feature_state)

    def get_feature_state_by_feature_name_or_id(
        self, feature: typing.Union[str, int]
    ) -> typing.Optional[FeatureStateModel]:
        def match_feature_state(fs):  # type: ignore[no-untyped-def]
            if isinstance(feature, int):
                return fs.feature.id == feature
            return fs.feature.name == feature

        feature_state = next(
            filter(
                match_feature_state,
                self.engine_identity_model.identity_features,
            ),
            None,
        )

        return feature_state

    def get_feature_state_by_featurestate_uuid(
        self, featurestate_uuid: str
    ) -> typing.Optional[FeatureStateModel]:
        return next(
            filter(
                lambda fs: str(fs.featurestate_uuid) == featurestate_uuid,  # type: ignore[arg-type,union-attr]
                self.engine_identity_model.identity_features,
            ),
            None,
        )

    def get_hash_key(self, use_identity_composite_key_for_hashing: bool) -> str:
        return self.engine_identity_model.get_hash_key(
            use_identity_composite_key_for_hashing
        )

    def remove_feature_override(self, feature_state: FeatureStateModel) -> None:
        with suppress(ValueError):  # ignore if feature state didn't exist
            self.engine_identity_model.identity_features.remove(feature_state)

    def save(self, user: FFAdminUser | APIKeyUser = None):  # type: ignore[no-untyped-def,assignment]
        self.dynamo_wrapper.put_item(self.to_document())
        changeset = self._get_changes()
        self._update_feature_overrides(
            changeset=changeset,
            user=user,
        )
        self._reset_initial_state()  # type: ignore[no-untyped-call]

    def delete(self, user: FFAdminUser | APIKeyUser = None) -> None:  # type: ignore[assignment]
        self.dynamo_wrapper.delete_item(self.engine_identity_model.composite_key)
        self.engine_identity_model.identity_features.clear()
        changeset = self._get_changes()
        self._update_feature_overrides(
            changeset=changeset,
            user=user,
        )
        self._reset_initial_state()  # type: ignore[no-untyped-call]

        if settings.CLICKHOUSE_ENABLED:
            from segment_membership.services import enqueue_membership_refresh

            enqueue_membership_refresh(
                self.environment.project,
                delay_until=(
                    timezone.now()
                    + timedelta(
                        seconds=settings.SEGMENT_MEMBERSHIP_DELETE_REFRESH_DELAY_SECONDS
                    )
                ),
            )

    def synchronise_features(self, valid_feature_names: typing.Collection[str]) -> None:
        identity_feature_names = {
            fs.feature.name for fs in self.engine_identity_model.identity_features
        }
        if not identity_feature_names.issubset(valid_feature_names):
            self.engine_identity_model.prune_features(list(valid_feature_names))
            sync_identity_document_features.delay(args=(str(self.identity_uuid),))

    def to_document(self) -> dict:  # type: ignore[type-arg]
        return map_engine_identity_to_identity_document(self.engine_identity_model)

    def _update_feature_overrides(
        self, changeset: IdentityChangeset, user: FFAdminUser | APIKeyUser
    ) -> None:
        if changeset["feature_overrides"]:
            # TODO: would this be simpler if we put a wrapper around FeatureStateModel instead?
            kwargs = {
                "environment_api_key": self.environment_api_key,
                "identifier": self.identifier,
                "user_id": (
                    user.id  # type: ignore[union-attr]
                    if not getattr(user, "is_master_api_key_user", False)
                    else None
                ),
                "changes": changeset,
                "identity_uuid": str(self.identity_uuid),
                "master_api_key_id": (
                    user.pk if getattr(user, "is_master_api_key_user", False) else None
                ),
            }
            generate_audit_log_records.delay(kwargs=kwargs)
            update_flagsmith_environments_v2_identity_overrides.delay(
                kwargs={
                    "environment_api_key": self.environment_api_key,
                    "changes": changeset,
                    "identity_uuid": str(self.identity_uuid),
                    "identifier": self.identifier,
                }
            )

    def _get_changes(self) -> IdentityChangeset:
        previous_instance = self._initial_state
        changes = {}  # type: ignore[var-annotated]
        feature_changes = changes.setdefault("feature_overrides", {})
        previous_feature_overrides = {
            fs.featurestate_uuid: fs for fs in previous_instance.feature_overrides
        }
        current_feature_overrides = {
            fs.featurestate_uuid: fs for fs in self.feature_overrides
        }
        environment = Environment.get_from_cache(self.environment_api_key)
        assert environment

        for uuid_, previous_fs in previous_feature_overrides.items():
            current_matching_fs = current_feature_overrides.get(uuid_)
            if current_matching_fs is None:
                feature_changes[previous_fs.feature.name] = generate_change_dict(
                    change_type="-",
                    edge_identity=self,
                    environment=environment,
                    old=previous_fs,
                )
            elif current_matching_fs.enabled != previous_fs.enabled or (
                get_edge_identity_override_value(
                    self, current_matching_fs, environment=environment
                )
                != get_edge_identity_override_value(
                    self, previous_fs, environment=environment
                )
            ):
                feature_changes[previous_fs.feature.name] = generate_change_dict(
                    change_type="~",
                    edge_identity=self,
                    environment=environment,
                    new=current_matching_fs,
                    old=previous_fs,
                )

        for uuid_, previous_fs in current_feature_overrides.items():
            if uuid_ not in previous_feature_overrides:
                feature_changes[previous_fs.feature.name] = generate_change_dict(
                    change_type="+",
                    edge_identity=self,
                    environment=environment,
                    new=previous_fs,
                )

        return changes  # type: ignore[return-value]

    def _reset_initial_state(self):  # type: ignore[no-untyped-def]
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
