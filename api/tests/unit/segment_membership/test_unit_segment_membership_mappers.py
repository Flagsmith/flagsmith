from decimal import Decimal

import pytest
from flagsmith_schemas.dynamodb import Identity as DynamoIdentity

from segment_membership.mappers import map_identity_document_to_clickhouse_row

UUID_A = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
UUID_B = "550e8400-e29b-41d4-a716-446655440000"


@pytest.mark.parametrize(
    "doc,expected",
    [
        pytest.param(
            {
                "identity_uuid": UUID_A,
                "identifier": "alice",
                "environment_api_key": "env-key",
                "composite_key": "env_x_alice",
                "created_date": "2026-05-08T00:00:00Z",
                "identity_traits": [
                    {"trait_key": "plan", "trait_value": "growth"},
                ],
            },
            ("env-key", "alice", "env_x_alice", {"plan": "growth"}),
            id="single string trait",
        ),
        pytest.param(
            {
                "identity_uuid": UUID_A,
                "identifier": "alice",
                "environment_api_key": "env-key",
                "composite_key": "env_x_alice",
                "created_date": "2026-05-08T00:00:00Z",
                "identity_traits": [],
            },
            ("env-key", "alice", "env_x_alice", None),
            id="empty traits collapse to NULL",
        ),
        pytest.param(
            {
                "identity_uuid": UUID_A,
                "identifier": "alice",
                "environment_api_key": "env-key",
                "composite_key": "env_x_alice",
                "created_date": "2026-05-08T00:00:00Z",
                "identity_traits": [
                    {"trait_key": "age", "trait_value": Decimal("18")},
                ],
            },
            ("env-key", "alice", "env_x_alice", {"age": 18}),
            id="whole-number Decimal narrows to int",
        ),
        pytest.param(
            {
                "identity_uuid": UUID_A,
                "identifier": "alice",
                "environment_api_key": "env-key",
                "composite_key": "env_x_alice",
                "created_date": "2026-05-08T00:00:00Z",
                "identity_traits": [
                    {"trait_key": "score", "trait_value": Decimal("1.5")},
                ],
            },
            ("env-key", "alice", "env_x_alice", {"score": 1.5}),
            id="fractional Decimal narrows to float",
        ),
        pytest.param(
            {
                "identity_uuid": UUID_A,
                "identifier": "alice",
                "environment_api_key": "env-key",
                "composite_key": "env_x_alice",
                "created_date": "2026-05-08T00:00:00Z",
                "identity_traits": [
                    {"trait_key": "plan", "trait_value": "growth"},
                    {"trait_key": "team", "trait_value": "alpha"},
                ],
            },
            (
                "env-key",
                "alice",
                "env_x_alice",
                {"plan": "growth", "team": "alpha"},
            ),
            id="multiple traits flatten to a single dict",
        ),
    ],
)
def test_map_identity_document_to_clickhouse_row__cases__return_expected(
    doc: DynamoIdentity,
    expected: tuple[str, str, str, dict[str, object] | None],
) -> None:
    # Given a Dynamo identity document
    # When mapped onto an IDENTITIES row
    env_id, _id, identifier, identity_key, traits = (
        map_identity_document_to_clickhouse_row("env-key", doc)
    )

    # Then non-id columns line up positionally with the IDENTITIES schema
    assert (env_id, identifier, identity_key, traits) == expected
    # ...and the id column is a stable signed 64-bit projection of the UUID
    assert -(2**63) <= _id < 2**63


def test_map_identity_document_to_clickhouse_row__same_uuid__same_id() -> None:
    # Given two documents sharing an identity_uuid
    doc: DynamoIdentity = {
        "identity_uuid": UUID_A,
        "identifier": "alice",
        "environment_api_key": "env-key",
        "composite_key": "env_x_alice",
        "created_date": "2026-05-08T00:00:00Z",
        "identity_traits": [],
    }

    # When mapped twice
    a = map_identity_document_to_clickhouse_row("env-a", doc)
    b = map_identity_document_to_clickhouse_row("env-b", doc)

    # Then the id projection is stable across calls
    assert a[1] == b[1]


def test_map_identity_document_to_clickhouse_row__different_uuid__different_id() -> (
    None
):
    # Given two documents with distinct identity_uuids
    doc_a: DynamoIdentity = {
        "identity_uuid": UUID_A,
        "identifier": "alice",
        "environment_api_key": "env-key",
        "composite_key": "env_x_alice",
        "created_date": "2026-05-08T00:00:00Z",
        "identity_traits": [],
    }
    doc_b: DynamoIdentity = {
        "identity_uuid": UUID_B,
        "identifier": "bob",
        "environment_api_key": "env-key",
        "composite_key": "env_x_bob",
        "created_date": "2026-05-08T00:00:00Z",
        "identity_traits": [],
    }

    # When mapped
    a = map_identity_document_to_clickhouse_row("env-key", doc_a)
    b = map_identity_document_to_clickhouse_row("env-key", doc_b)

    # Then the id projections are distinct
    assert a[1] != b[1]
