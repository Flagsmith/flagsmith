from datetime import datetime
from decimal import Decimal

from flagsmith_schemas import dynamodb

from segment_membership.types import ClickHouseIdentityRow


def map_identity_document_to_clickhouse_row(
    env_key: str,
    identity_doc: dynamodb.Identity,
    inserted_at: datetime,
) -> ClickHouseIdentityRow:
    """Project a Dynamo identity document onto an IDENTITIES row tuple."""
    identifier = identity_doc["identifier"]
    composite_key = identity_doc["composite_key"]
    raw_traits = identity_doc.get("identity_traits")
    traits = _flatten_traits(raw_traits) if raw_traits else None
    return (
        env_key,
        identifier,
        composite_key,
        traits,
        inserted_at,
    )


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
