from datetime import datetime, timezone
from decimal import Decimal

import pytest
from flagsmith_schemas.dynamodb import Identity as DynamoIdentity

from segment_membership.mappers import map_identity_document_to_clickhouse_row
from segment_membership.types import ClickHouseIdentityRow

UUID_A = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
INSERTED_AT = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)


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
            ("env-key", "alice", "env_x_alice", {"plan": "growth"}, INSERTED_AT),
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
            ("env-key", "alice", "env_x_alice", None, INSERTED_AT),
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
            ("env-key", "alice", "env_x_alice", {"age": 18}, INSERTED_AT),
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
            ("env-key", "alice", "env_x_alice", {"score": 1.5}, INSERTED_AT),
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
                INSERTED_AT,
            ),
            id="multiple traits flatten to a single dict",
        ),
    ],
)
def test_map_identity_document_to_clickhouse_row__cases__return_expected(
    doc: DynamoIdentity,
    expected: ClickHouseIdentityRow,
) -> None:
    # Given
    # When
    # Then
    assert (
        map_identity_document_to_clickhouse_row("env-key", doc, INSERTED_AT) == expected
    )
