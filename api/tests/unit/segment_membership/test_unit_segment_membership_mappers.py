from decimal import Decimal

import pytest
from flagsmith_schemas.dynamodb import Identity as DynamoIdentity

from segment_membership.mappers import map_identity_document_to_clickhouse_row

UUID_A = "f47ac10b-58cc-4372-a567-0e02b2c3d479"


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
    # Then it lines up positionally with the IDENTITIES schema
    assert map_identity_document_to_clickhouse_row("env-key", doc) == expected
