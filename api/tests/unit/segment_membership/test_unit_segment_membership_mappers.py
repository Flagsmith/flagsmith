from decimal import Decimal

from flagsmith_schemas.dynamodb import Identity as DynamoIdentity

from segment_membership.mappers import (
    _coerce_trait_value,
    _flatten_traits,
    _identity_id,
    map_identity_document_to_snowflake_row,
)


def test_identity_id__same_uuid__produces_same_id() -> None:
    # Given the same identity_uuid
    uuid = "abc-123"

    # When the helper runs twice
    a = _identity_id(uuid)
    b = _identity_id(uuid)

    # Then the result is identical and fits in a non-negative 64-bit int
    assert a == b
    assert 0 <= a < 2**64


def test_coerce_trait_value__decimal_int__narrows_to_int() -> None:
    # Given a Decimal that's a whole number
    # When coerced
    # Then it becomes a plain int
    assert _coerce_trait_value(Decimal("3")) == 3
    assert isinstance(_coerce_trait_value(Decimal("3")), int)


def test_coerce_trait_value__decimal_fraction__narrows_to_float() -> None:
    # Given a Decimal with a fractional component
    # When coerced
    # Then it becomes a float
    assert _coerce_trait_value(Decimal("1.5")) == 1.5
    assert isinstance(_coerce_trait_value(Decimal("1.5")), float)


def test_coerce_trait_value__non_decimal__passes_through_unchanged() -> None:
    # Given a value that isn't a Decimal
    # When coerced
    # Then it passes through unchanged
    assert _coerce_trait_value("growth") == "growth"
    assert _coerce_trait_value(True) is True


def test_flatten_traits__none__returns_empty_dict() -> None:
    # Given no traits
    # When flattened
    # Then the result is an empty dict
    assert _flatten_traits(None) == {}


def test_flatten_traits__list__returns_dict_dropping_empty_keys() -> None:
    # Given a Dynamo trait list with one well-formed and one empty-key entry
    # When flattened
    # Then only the well-formed entry survives
    assert _flatten_traits(
        [
            {"trait_key": "plan", "trait_value": "growth"},
            {"trait_key": "", "trait_value": "skipped"},
        ]
    ) == {"plan": "growth"}


def test_map_identity_document_to_snowflake_row__with_traits__returns_tuple() -> None:
    # Given a Dynamo identity document with traits
    doc: DynamoIdentity = {
        "identity_uuid": "uuid-1",
        "identifier": "alice",
        "environment_api_key": "env-key",
        "composite_key": "env_x_alice",
        "created_date": "2026-05-08T00:00:00Z",
        "identity_traits": [{"trait_key": "plan", "trait_value": "growth"}],
    }

    # When mapped
    env_id, _id, identifier, identity_key, traits = (
        map_identity_document_to_snowflake_row("env-key", doc)
    )

    # Then the columns line up positionally with the IDENTITIES schema
    assert env_id == "env-key"
    assert _id == _identity_id("uuid-1")
    assert identifier == "alice"
    assert identity_key == "env_x_alice"
    assert traits == {"plan": "growth"}


def test_map_identity_document_to_snowflake_row__no_traits__returns_none_for_traits() -> (
    None
):
    # Given a Dynamo identity document with no trait entries
    doc: DynamoIdentity = {
        "identity_uuid": "uuid-1",
        "identifier": "alice",
        "environment_api_key": "env-key",
        "composite_key": "env_x_alice",
        "created_date": "2026-05-08T00:00:00Z",
        "identity_traits": [],
    }

    # When mapped
    *_, traits = map_identity_document_to_snowflake_row("env-key", doc)

    # Then the traits VARIANT slot is None (NULL)
    assert traits is None


def test_map_identity_document_to_snowflake_row__no_composite_key__falls_back_to_uuid() -> (
    None
):
    # Given an identity document missing the composite_key
    doc: DynamoIdentity = {  # type: ignore[typeddict-item]
        "identity_uuid": "uuid-1",
        "identifier": "alice",
        "environment_api_key": "env-key",
        "created_date": "2026-05-08T00:00:00Z",
        "identity_traits": [],
    }

    # When mapped
    *_, identity_key, _traits = map_identity_document_to_snowflake_row("env-key", doc)

    # Then identity_key falls back to identity_uuid
    assert identity_key == "uuid-1"
