from collections.abc import Mapping
from decimal import Decimal
from typing import TYPE_CHECKING, Any, TypeVar, cast

from django.utils import timezone
from flagsmith_schemas.dynamodb import (
    Environment,
    EnvironmentAPIKey,
    EnvironmentCompressed,
    EnvironmentV2IdentityOverride,
    EnvironmentV2MetaCompressed,
    FeatureState,
    Identity,
)
from pydantic import TypeAdapter

from edge_api.identities.types import IdentityChangeset
from environments.dynamodb.constants import (
    ENVIRONMENTS_V2_ENVIRONMENT_META_DOCUMENT_KEY,
)
from environments.dynamodb.types import (
    IdentityOverridesV2Changeset,
    IdentityOverrideV2,
)
from environments.dynamodb.utils import (
    estimate_document_size,
    get_environments_v2_identity_override_document_key,
)
from util.dataclasses import CompressedEnvironmentDocument
from util.mappers.engine import (
    map_environment_api_key_to_engine,
    map_environment_to_engine,
    map_identity_to_engine,
)
from util.mappers.types import Document

if TYPE_CHECKING:
    from environments.identities.models import Identity as IdentityModel
    from environments.models import Environment as EnvironmentModel
    from environments.models import EnvironmentAPIKey as EnvironmentAPIKeyModel


__all__ = (
    "map_engine_identity_to_identity_document",
    "map_identity_document_to_engine_identity",
    "map_identity_override_document_to_identity_override",
    "map_environment_api_key_to_environment_api_key_document",
    "map_environment_to_compressed_environment_document",
    "map_environment_to_compressed_environment_v2_document",
    "map_environment_to_environment_document",
    "map_environment_to_environment_v2_document",
    "map_identity_to_identity_document",
)


T = TypeVar("T")

_environment_adapter: TypeAdapter[Environment] = TypeAdapter(Environment)
_environment_api_key_adapter: TypeAdapter[EnvironmentAPIKey] = TypeAdapter(
    EnvironmentAPIKey
)
_identity_adapter: TypeAdapter[Identity] = TypeAdapter(Identity)
_identity_override_adapter: TypeAdapter[EnvironmentV2IdentityOverride] = TypeAdapter(
    EnvironmentV2IdentityOverride
)
_environment_compressed_adapter: TypeAdapter[EnvironmentCompressed] = TypeAdapter(
    EnvironmentCompressed,
)
_environment_v2_meta_compressed_adapter: TypeAdapter[EnvironmentV2MetaCompressed] = (
    TypeAdapter(EnvironmentV2MetaCompressed)
)

_NULLABLE_IDENTITY_KEY_ATTRIBUTES = {"dashboard_alias", "system_traits"}


def map_environment_to_environment_document(
    environment: "EnvironmentModel",
) -> Document:
    return cast(
        Document,
        _environment_adapter.validate_python(map_environment_to_engine(environment)),
    )


def map_environment_to_compressed_environment_document(
    environment: "EnvironmentModel",
) -> CompressedEnvironmentDocument:
    return _get_compressed_environment_document(
        document=map_environment_to_environment_document(environment),
        adapter=_environment_compressed_adapter,
    )


def map_environment_to_environment_v2_document(
    environment: "EnvironmentModel",
) -> Document:
    environment_document = map_environment_to_environment_document(environment)
    environment_api_key = environment_document.pop("api_key")
    return {
        **environment_document,
        "document_key": ENVIRONMENTS_V2_ENVIRONMENT_META_DOCUMENT_KEY,
        "environment_api_key": environment_api_key,
        "environment_id": str(environment.id),
    }


def map_environment_to_compressed_environment_v2_document(
    environment: "EnvironmentModel",
) -> CompressedEnvironmentDocument:
    return _get_compressed_environment_document(
        document=map_environment_to_environment_v2_document(environment),
        adapter=_environment_v2_meta_compressed_adapter,
    )


def map_environment_api_key_to_environment_api_key_document(
    environment_api_key: "EnvironmentAPIKeyModel",
) -> Document:
    return cast(
        Document,
        _environment_api_key_adapter.validate_python(
            map_environment_api_key_to_engine(environment_api_key)
        ),
    )


def map_identity_document_to_engine_identity(
    identity_document: Mapping[str, Any],
) -> Identity:
    return _validate_document(_identity_adapter, identity_document)


def map_engine_identity_to_identity_document(
    engine_identity: Mapping[str, Any],
) -> Document:
    identity_document = cast(
        Document, _validate_document(_identity_adapter, engine_identity)
    )
    return {
        field_name: value
        for field_name, value in identity_document.items()
        if value is not None or field_name not in _NULLABLE_IDENTITY_KEY_ATTRIBUTES
    }


def map_identity_to_identity_document(
    identity: "IdentityModel",
) -> Document:
    return map_engine_identity_to_identity_document(map_identity_to_engine(identity))


def map_identity_override_document_to_identity_override(
    identity_override_document: Mapping[str, Any],
) -> IdentityOverrideV2:
    return _validate_document(_identity_override_adapter, identity_override_document)


def map_engine_feature_state_to_identity_override(
    *,
    feature_state: Mapping[str, Any] | FeatureState,
    identity_uuid: str,
    identifier: str,
    environment_api_key: str,
    environment_id: int,
) -> IdentityOverrideV2:
    return map_identity_override_document_to_identity_override(
        {
            "environment_id": str(environment_id),
            "document_key": get_environments_v2_identity_override_document_key(
                feature_id=int(feature_state["feature"]["id"]),
                identity_uuid=identity_uuid,
            ),
            "environment_api_key": environment_api_key,
            "identifier": identifier,
            "identity_uuid": identity_uuid,
            "feature_state": feature_state,
            "created_date": timezone.now(),
        }
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
                to_delete.append(
                    map_engine_feature_state_to_identity_override(
                        feature_state=change_details["old"],
                        identity_uuid=identity_uuid,
                        identifier=identifier,
                        environment_api_key=environment_api_key,
                        environment_id=environment_id,
                    )
                )
            case _:
                to_put.append(
                    map_engine_feature_state_to_identity_override(
                        feature_state=change_details["new"],
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
    return cast(Document, identity_override)


def _validate_document(adapter: TypeAdapter[T], document: Mapping[str, Any]) -> T:
    # The schema doesn't round-trip stored numbers, e.g. it validates an integer
    # `Decimal` feature value as a string, so they're validated as native numbers.
    return adapter.validate_python(_map_decimals_to_numbers(document))


def _map_decimals_to_numbers(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value) if value.as_tuple().exponent else int(value)
    if isinstance(value, Mapping):
        return {key: _map_decimals_to_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_map_decimals_to_numbers(item) for item in value]
    return value


def _get_compressed_environment_document(
    document: Document,
    adapter: "TypeAdapter[Any]",
) -> CompressedEnvironmentDocument:
    uncompressed_size_bytes = estimate_document_size(document)
    document["compressed"] = True
    compressed_document = adapter.validate_python(document)
    compressed_size_bytes = estimate_document_size(compressed_document)
    return CompressedEnvironmentDocument(
        document=cast(Document, compressed_document),
        compressed_size_bytes=compressed_size_bytes,
        compression_ratio=compressed_size_bytes / uncompressed_size_bytes,
    )
