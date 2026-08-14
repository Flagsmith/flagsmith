from typing import Any

import pytest
import responses as responses_lib

from trust_relationships.constants import DISCOVERY_TIMEOUT_SECONDS
from trust_relationships.exceptions import InvalidTokenError
from trust_relationships.oidc import get_jwks_client, match_claim_rules


@pytest.mark.parametrize(
    "claims, claim_rules, expected",
    [
        pytest.param({}, [], True, id="no-rules-always-match"),
        pytest.param(
            {"repository": "Flagsmith/flagsmith"},
            [{"claim": "repository", "values": ["Flagsmith/flagsmith"]}],
            True,
            id="exact-match",
        ),
        pytest.param(
            {"repository": "Flagsmith/flagsmith"},
            [{"claim": "repository", "values": ["Flagsmith/*"]}],
            True,
            id="glob-match",
        ),
        pytest.param(
            {"repository": "Flagsmith/flagsmith"},
            [{"claim": "repository", "values": ["SomeoneElse/*", "Flagsmith/*"]}],
            True,
            id="any-value-matches",
        ),
        pytest.param(
            {"repository": "SomeoneElse/repo"},
            [{"claim": "repository", "values": ["Flagsmith/*"]}],
            False,
            id="value-mismatch",
        ),
        pytest.param(
            {},
            [{"claim": "repository", "values": ["Flagsmith/*"]}],
            False,
            id="missing-claim",
        ),
        pytest.param(
            {"repository": "Flagsmith/flagsmith", "environment": "staging"},
            [
                {"claim": "repository", "values": ["Flagsmith/*"]},
                {"claim": "environment", "values": ["production"]},
            ],
            False,
            id="all-rules-must-match",
        ),
        pytest.param(
            {"groups": ["deployers", "admins"]},
            [{"claim": "groups", "values": ["deployers"]}],
            True,
            id="list-claim-any-element",
        ),
        pytest.param(
            {"run_attempt": 1},
            [{"claim": "run_attempt", "values": ["1"]}],
            True,
            id="non-string-claim-stringified",
        ),
    ],
)
def test_match_claim_rules__various_rules__returns_expected(
    claims: dict[str, Any],
    claim_rules: list[dict[str, Any]],
    expected: bool,
) -> None:
    # Given / When
    result = match_claim_rules(claims, claim_rules)

    # Then
    assert result is expected


def test_get_jwks_client__valid_discovery__applies_discovery_timeout(
    responses: responses_lib.RequestsMock,
) -> None:
    # Given
    issuer = "https://timeout.example.com"
    responses.add(
        responses_lib.GET,
        f"{issuer}/.well-known/openid-configuration",
        json={"jwks_uri": f"{issuer}/.well-known/jwks"},
    )

    # When
    client = get_jwks_client(issuer)

    # Then: PyJWKClient would otherwise fetch keys on its own 30s default
    assert client.timeout == DISCOVERY_TIMEOUT_SECONDS


def test_get_jwks_client__discovery_error__raises_invalid(
    responses: responses_lib.RequestsMock,
) -> None:
    # Given
    issuer = "https://broken.example.com"
    responses.add(
        responses_lib.GET,
        f"{issuer}/.well-known/openid-configuration",
        status=500,
    )

    # When / Then
    with pytest.raises(InvalidTokenError):
        get_jwks_client(issuer)


def test_get_jwks_client__missing_jwks_uri__raises_invalid(
    responses: responses_lib.RequestsMock,
) -> None:
    # Given
    issuer = "https://incomplete.example.com"
    responses.add(
        responses_lib.GET,
        f"{issuer}/.well-known/openid-configuration",
        json={"issuer": issuer},
    )

    # When / Then
    with pytest.raises(InvalidTokenError):
        get_jwks_client(issuer)


def test_get_jwks_client__non_https_jwks_uri__raises_invalid(
    responses: responses_lib.RequestsMock,
) -> None:
    # Given
    issuer = "https://sneaky.example.com"
    responses.add(
        responses_lib.GET,
        f"{issuer}/.well-known/openid-configuration",
        json={"jwks_uri": "http://sneaky.example.com/jwks"},
    )

    # When / Then
    with pytest.raises(InvalidTokenError):
        get_jwks_client(issuer)
