import uuid
from decimal import Decimal

from flagsmith_schemas import dynamodb

# (environment_id, id, identifier, identity_key, traits)
SnowflakeIdentityRow = tuple[str, int, str, str, dict[str, object] | None]


def map_identity_document_to_snowflake_row(
    env_key: str,
    identity_doc: dynamodb.Identity,
) -> SnowflakeIdentityRow:
    """Project a Dynamo identity document onto the canonical IDENTITIES
    row tuple. The returned tuple aligns positionally with the schema
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
    """Project a UUID onto a stable signed 64-bit IDENTITIES.id."""
    return int.from_bytes(uuid.UUID(identity_uuid).bytes[:8], "big", signed=True)


def _coerce_trait_value(value: object) -> object:
    """Coerce Dynamo-decoded values for VARIANT serialisation. boto3
    returns `Decimal` for numbers; we narrow to int when whole, float
    otherwise, so the VARIANT keeps a useful numeric type."""
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value


def _flatten_traits(
    identity_traits: list[dynamodb.Trait],
) -> dict[str, object]:
    """Convert Dynamo's `[{trait_key, trait_value}, ...]` list into a
    flat trait map."""
    return {
        t["trait_key"]: _coerce_trait_value(t.get("trait_value"))
        for t in identity_traits
    }
