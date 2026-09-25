import copy
import typing
import uuid
from contextlib import suppress
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from flag_engine.context.mappers import map_any_value_to_context_value
from flagsmith_schemas.dynamodb import FeatureState, Identity

from api_keys.user import APIKeyUser
from edge_api.identities.exceptions import DuplicateFeatureState
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
from util.mappers import (
    map_engine_identity_to_identity_document,
    map_identifier_to_engine,
    map_identity_document_to_engine_identity,
)


def new_feature_override(**fields: typing.Any) -> FeatureState:
    """An identity override's fields, defaulted as for a new one."""
    return typing.cast(
        FeatureState,
        {
            "django_id": None,
            "feature_segment": None,
            "featurestate_uuid": str(uuid.uuid4()),
            "feature_state_value": None,
            **fields,
            "multivariate_feature_state_values": [
                {"mv_fs_value_uuid": str(uuid.uuid4()), **mv_fs_value}
                for mv_fs_value in fields.get("multivariate_feature_state_values", [])
            ],
        },
    )


class EdgeIdentity:
    dynamo_wrapper = DynamoIdentityWrapper()

    def __init__(self, document: Identity):
        document.setdefault("identity_features", [])
        self.document = document
        self._reset_initial_state()  # type: ignore[no-untyped-call]

    @classmethod
    def create(
        cls, identifier: str, environment_api_key: str, **fields: typing.Any
    ) -> "EdgeIdentity":
        return cls.from_identity_document(
            {
                "identifier": identifier,
                "environment_api_key": environment_api_key,
                **fields,
            }
        )

    @classmethod
    def from_identity_document(
        cls, identity_document: typing.Mapping[str, typing.Any]
    ) -> "EdgeIdentity":
        return EdgeIdentity(
            map_identity_document_to_engine_identity(
                map_identifier_to_engine(**identity_document)
            )
        )

    @property
    def environment_api_key(self) -> str:
        return self.document["environment_api_key"]

    @property
    def feature_overrides(self) -> list[FeatureState]:
        return self.document["identity_features"]

    @property
    def id(self) -> typing.Union[int, str]:
        django_id = self.document.get("django_id")
        return int(django_id) if django_id else self.identity_uuid

    @property
    def identifier(self) -> str:
        return self.document["identifier"]

    @property
    def identity_uuid(self) -> str:
        return self.document["identity_uuid"]

    @property
    def environment(self) -> Environment:
        environment: Environment = Environment.objects.get(
            api_key=self.environment_api_key
        )
        return environment

    @property
    def dashboard_alias(self) -> str | None:
        return self.document.get("dashboard_alias")

    @dashboard_alias.setter
    def dashboard_alias(self, dashboard_alias: str) -> None:
        self.document["dashboard_alias"] = dashboard_alias

    def add_feature_override(self, feature_state: FeatureState) -> None:
        feature_id = feature_state["feature"]["id"]
        if any(fs["feature"]["id"] == feature_id for fs in self.feature_overrides):
            raise DuplicateFeatureState(
                f"Feature state for feature id={feature_id} already exists"
            )
        self.feature_overrides.append(feature_state)

    def get_feature_state_by_feature_name_or_id(
        self, feature: typing.Union[str, int]
    ) -> typing.Optional[FeatureState]:
        key = "id" if isinstance(feature, int) else "name"
        return next(
            (fs for fs in self.feature_overrides if fs["feature"][key] == feature),  # type: ignore[literal-required]
            None,
        )

    def get_feature_state_by_featurestate_uuid(
        self, featurestate_uuid: str
    ) -> typing.Optional[FeatureState]:
        return next(
            (
                fs
                for fs in self.feature_overrides
                if str(fs.get("featurestate_uuid")) == featurestate_uuid
            ),
            None,
        )

    def get_hash_key(self, use_identity_composite_key_for_hashing: bool) -> str:
        if use_identity_composite_key_for_hashing:
            return self.document["composite_key"]
        if (django_id := self.document.get("django_id")) is not None:
            return str(django_id)
        return self.identifier

    def update_traits(
        self, traits: typing.Iterable[typing.Mapping[str, typing.Any]]
    ) -> bool:
        """Set, or unset if their value is `None`, traits; return whether any changed."""
        existing_traits = {
            trait["trait_key"]: trait for trait in self.document["identity_traits"]
        }
        traits_changed = False
        for trait in traits:
            trait_key, trait_value = trait["trait_key"], trait["trait_value"]
            existing_trait = existing_traits.get(trait_key)
            if trait_value is None:
                traits_changed |= existing_traits.pop(trait_key, None) is not None
            elif (
                existing_trait is None
                or map_any_value_to_context_value(existing_trait["trait_value"])
                != trait_value
            ):
                existing_traits[trait_key] = {
                    "trait_key": trait_key,
                    "trait_value": trait_value,
                }
                traits_changed = True
        self.document["identity_traits"] = list(existing_traits.values())
        return traits_changed

    def remove_feature_override(self, feature_state: FeatureState) -> None:
        with suppress(ValueError):  # ignore if feature state didn't exist
            self.feature_overrides.remove(feature_state)

    def save(self, user: FFAdminUser | APIKeyUser = None):  # type: ignore[no-untyped-def,assignment]
        self.dynamo_wrapper.put_item(self.to_document())
        changeset = self._get_changes()
        self._update_feature_overrides(
            changeset=changeset,
            user=user,
        )
        self._reset_initial_state()  # type: ignore[no-untyped-call]

    def delete(self, user: FFAdminUser | APIKeyUser = None) -> None:  # type: ignore[assignment]
        self.dynamo_wrapper.delete_item(self.document["composite_key"])
        self.feature_overrides.clear()
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
            fs["feature"]["name"] for fs in self.feature_overrides
        }
        if not identity_feature_names.issubset(valid_feature_names):
            self.document["identity_features"] = [
                fs
                for fs in self.feature_overrides
                if fs["feature"]["name"] in valid_feature_names
            ]
            sync_identity_document_features.delay(args=(str(self.identity_uuid),))

    def to_document(self) -> dict[str, typing.Any]:
        return map_engine_identity_to_identity_document(self.document)

    def _update_feature_overrides(
        self, changeset: IdentityChangeset, user: FFAdminUser | APIKeyUser
    ) -> None:
        if changeset["feature_overrides"]:
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
            fs.get("featurestate_uuid"): fs
            for fs in previous_instance.feature_overrides
        }
        current_feature_overrides = {
            fs.get("featurestate_uuid"): fs for fs in self.feature_overrides
        }
        environment = Environment.get_from_cache(self.environment_api_key)
        assert environment

        for uuid_, previous_fs in previous_feature_overrides.items():
            current_matching_fs = current_feature_overrides.get(uuid_)
            if current_matching_fs is None:
                feature_changes[previous_fs["feature"]["name"]] = generate_change_dict(
                    change_type="-",
                    edge_identity=self,
                    environment=environment,
                    old=previous_fs,
                )
            elif current_matching_fs["enabled"] != previous_fs["enabled"] or (
                get_edge_identity_override_value(
                    self, current_matching_fs, environment=environment
                )
                != get_edge_identity_override_value(
                    self, previous_fs, environment=environment
                )
            ):
                feature_changes[previous_fs["feature"]["name"]] = generate_change_dict(
                    change_type="~",
                    edge_identity=self,
                    environment=environment,
                    new=current_matching_fs,
                    old=previous_fs,
                )

        for uuid_, previous_fs in current_feature_overrides.items():
            if uuid_ not in previous_feature_overrides:
                feature_changes[previous_fs["feature"]["name"]] = generate_change_dict(
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
            self.add_feature_override(
                new_feature_override(
                    feature=feature_in_source["feature"],
                    feature_state_value=feature_in_source["feature_state_value"],
                    enabled=feature_in_source["enabled"],
                    multivariate_feature_state_values=copy.deepcopy(
                        feature_in_source.get("multivariate_feature_state_values", [])
                    ),
                )
            )
