from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, TypeAlias, TypeVar, Union

from flag_engine.features.models import FeatureStateModel
from pydantic import BaseModel

from edge_api.identities.types import IdentityChangeset
from environments.dynamodb.constants import (
    ENVIRONMENTS_V2_ENVIRONMENT_META_DOCUMENT_KEY,
)
from environments.dynamodb.types import (
    IdentityOverridesV2Changeset,
    IdentityOverrideV2,
)
from environments.dynamodb.utils import (
    get_environments_v2_identity_override_document_key,
)
from util.mappers.engine import (
    map_environment_api_key_to_engine,
    map_environment_to_engine,
    map_identity_to_engine,
)

if TYPE_CHECKING:
    from flag_engine.identities.models import IdentityModel

    from environments.identities.models import Identity
    from environments.models import Environment, EnvironmentAPIKey


__all__ = (
    "map_engine_identity_to_identity_document",
    "map_environment_api_key_to_environment_api_key_document",
    "map_environment_to_environment_document",
    "map_environment_to_environment_v2_document",
    "map_identity_to_identity_document",
)

DocumentValue: TypeAlias = Union[Dict[str, "DocumentValue"], str, bool, None, Decimal]
Document: TypeAlias = Dict[str, DocumentValue]


def map_environment_to_environment_document(
    environment: "Environment",
) -> Document:
    return {
        field_name: _map_value_to_document_value(value)
        for field_name, value in map_environment_to_engine(
            environment,
            with_integrations=True,
        )
    }


def map_environment_to_environment_v2_document(
    environment: "Environment",
) -> Document:
    environment_document = map_environment_to_environment_document(environment)
    environment_api_key = environment_document.pop("api_key")
    return {
        **environment_document,
        "document_key": ENVIRONMENTS_V2_ENVIRONMENT_META_DOCUMENT_KEY,
        "environment_api_key": environment_api_key,
        "environment_id": str(environment.id),
    }


def map_environment_api_key_to_environment_api_key_document(
    environment_api_key: "EnvironmentAPIKey",
) -> Document:
    return {
        field_name: _map_value_to_document_value(value)
        for field_name, value in map_environment_api_key_to_engine(environment_api_key)
    }


def map_engine_identity_to_identity_document(
    engine_identity: "IdentityModel",
) -> Document:
    response = {
        field_name: _map_value_to_document_value(value)
        for field_name, value in engine_identity
    }
    response["composite_key"] = engine_identity.composite_key
    return response


def map_identity_to_identity_document(
    identity: "Identity",
) -> Document:
    return map_engine_identity_to_identity_document(map_identity_to_engine(identity))


def map_engine_feature_state_to_identity_override(
    *,
    feature_state: "FeatureStateModel",
    identity_uuid: str,
    identifier: str,
    environment_api_key: str,
    environment_id: int,
) -> IdentityOverrideV2:
    return IdentityOverrideV2(
        document_key=get_environments_v2_identity_override_document_key(
            feature_id=feature_state.feature.id,
            identity_uuid=identity_uuid,
        ),
        environment_id=str(environment_id),
        environment_api_key=environment_api_key,
        feature_state=feature_state,
        identifier=identifier,
        identity_uuid=identity_uuid,
    )


def map_identity_changeset_to_identity_override_changeset(
    *,
    identity_changeset: "IdentityChangeset",
    identity_uuid: str,
    identifier: str,
    environment_api_key: str,
    environment_id: int,
) -> "IdentityOverridesV2Changeset":
    to_delete: list[IdentityOverrideV2] = []
    to_put: list[IdentityOverrideV2] = []

    for _, change_details in identity_changeset["feature_overrides"].items():
        match change_details["change_type"]:
            case "-":
                feature_state = FeatureStateModel.parse_obj(change_details["old"])
                to_delete.append(
                    map_engine_feature_state_to_identity_override(
                        feature_state=feature_state,
                        identity_uuid=identity_uuid,
                        identifier=identifier,
                        environment_api_key=environment_api_key,
                        environment_id=environment_id,
                    )
                )
            case _:
                feature_state = FeatureStateModel.parse_obj(change_details["new"])
                to_put.append(
                    map_engine_feature_state_to_identity_override(
                        feature_state=feature_state,
                        identity_uuid=identity_uuid,
                        identifier=identifier,
                        environment_api_key=environment_api_key,
                        environment_id=environment_id,
                    )
                )

    return IdentityOverridesV2Changeset(to_delete=to_delete, to_put=to_put)


def map_identity_override_to_identity_override_document(
    identity_override: IdentityOverrideV2,
) -> Document:
    return {
        field_name: _map_value_to_document_value(value)
        for field_name, value in identity_override
    }


T = TypeVar("T")


def _noop_encoder(value: T) -> T:
    return value


def _base_model_encoder(value: BaseModel) -> DocumentValue:
    return _map_value_to_document_value(value.dict())


def _dict_encoder(value: Dict[str, Any]) -> Dict[str, DocumentValue]:
    return {f_name: _map_value_to_document_value(val) for f_name, val in value.items()}


def _list_encoder(value: List[Any]) -> List[DocumentValue]:
    return [_map_value_to_document_value(item) for item in value]


def _decimal_encoder(value: Union[int, float]) -> Decimal:
    return Decimal(str(value))


def _isoformat_encoder(value: datetime) -> str:
    return value.isoformat()


DOCUMENT_VALUE_ENCODERS_BY_TYPE = {
    BaseModel: _base_model_encoder,
    dict: _dict_encoder,
    list: _list_encoder,
    type(None): _noop_encoder,
    str: _noop_encoder,
    bool: _noop_encoder,
    int: _decimal_encoder,
    float: _decimal_encoder,
    datetime: _isoformat_encoder,
    Decimal: _noop_encoder,
}


def _map_value_to_document_value(value: Any) -> DocumentValue:
    for base in value.__class__.__mro__[:-1]:
        try:
            encoder = DOCUMENT_VALUE_ENCODERS_BY_TYPE[base]
        except KeyError:
            continue
        return encoder(value)
    else:
        return str(value)
