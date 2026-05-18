import uuid
from decimal import Decimal

from flagsmith_schemas import dynamodb

# (environment_id, id, identifier, identity_key, traits)
ClickHouseIdentityRow = tuple[str, int, str, str, dict[str, object] | None]


def map_identity_document_to_clickhouse_row(
    env_key: str,
    identity_doc: dynamodb.Identity,
) -> ClickHouseIdentityRow:
    """Project a Dynamo identity document onto an IDENTITIES row tuple
    `(environment_id, id, identifier, identity_key, traits)`."""
    identity_uuid = identity_doc["identity_uuid"]
    identifier = identity_doc["identifier"]
    composite_key = identity_doc["composite_key"]
    raw_traits = identity_doc.get("identity_traits")
    traits = _flatten_traits(raw_traits) if raw_traits else None
    return (
        env_key,
        _identity_id(identity_uuid),
        identifier,
        composite_key,
        traits,
    )


def _identity_id(identity_uuid: str) -> int:
    # UInt64 column refuses negatives.
    return int.from_bytes(uuid.UUID(identity_uuid).bytes[:8], "big", signed=False)


def _coerce_trait_value(value: object) -> object:
    # boto3 hands us `Decimal` for numbers; narrow so the JSON column
    # stores a typed numeric subcolumn instead of failing to serialise.
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value


def _flatten_traits(
    identity_traits: list[dynamodb.Trait],
) -> dict[str, object]:
    return {
        t["trait_key"]: _coerce_trait_value(t.get("trait_value"))
        for t in identity_traits
    }
