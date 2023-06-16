from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, TypeAlias, TypeVar, Union

from pydantic import BaseModel

from mappers.engine import (
    map_environment_api_key_to_engine,
    map_environment_to_engine,
    map_identity_to_engine,
)

if TYPE_CHECKING:  # pragma: no cover
    from flag_engine.identities.models import IdentityModel

    from environments.identities.models import Identity
    from environments.models import Environment, EnvironmentAPIKey


__all__ = (
    "map_engine_identity_to_identity_document",
    "map_environment_api_key_to_environment_api_key_document",
    "map_environment_to_environment_document",
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
        )
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
    return {
        field_name: _map_value_to_document_value(value)
        for field_name, value in engine_identity
    }


def map_identity_to_identity_document(
    identity: "Identity",
) -> Document:
    return map_engine_identity_to_identity_document(map_identity_to_engine(identity))


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
