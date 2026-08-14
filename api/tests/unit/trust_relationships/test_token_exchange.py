import jwt
import pytest
import responses as responses_lib
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from organisations.models import Organisation
from tests.test_helpers import OIDCIssuerStub
from trust_relationships.exceptions import (
    InvalidTokenError,
    NoMatchingTrustRelationshipError,
)
from trust_relationships.models import TrustRelationship
from trust_relationships.services import (
    create_trust_relationship,
    decode_access_token,
    exchange_oidc_token,
)


def test_exchange_oidc_token__matching_token__returns_access_token(
    oidc_issuer: OIDCIssuerStub,
    github_trust_relationship: TrustRelationship,
    log: StructuredLogCapture,
) -> None:
    # Given
    token = oidc_issuer.sign_token(
        aud="https://github.com/Flagsmith",
        sub="repo:Flagsmith/flagsmith:ref:refs/heads/main",
        repository="Flagsmith/flagsmith",
    )

    # When
    result = exchange_oidc_token(token)

    # Then
    assert result.expires_in == 3600
    access_token_claims = decode_access_token(result.access_token)
    assert access_token_claims["trust_relationship_id"] == github_trust_relationship.id
    assert access_token_claims["sub"] == "repo:Flagsmith/flagsmith:ref:refs/heads/main"
    assert log.has(
        "token.exchanged",
        organisation__id=github_trust_relationship.organisation_id,
        trust_relationship__id=github_trust_relationship.id,
        token__sub="repo:Flagsmith/flagsmith:ref:refs/heads/main",
    )


def test_exchange_oidc_token__issuer_with_trailing_slash__matches(
    organisation: Organisation,
    responses: responses_lib.RequestsMock,
    mocker: MockerFixture,
) -> None:
    # Given: a trust relationship whose issuer ends in a slash, as Auth0's does
    issuer = "https://tenant.eu.auth0.com/"
    trust_relationship = create_trust_relationship(
        organisation_id=organisation.id,
        name="Auth0",
        issuer=issuer,
        audience="https://api.flagsmith.com",
        is_admin=True,
        claim_rules=[],
    )
    oidc_issuer = OIDCIssuerStub(issuer)
    responses.add(
        responses_lib.GET,
        "https://tenant.eu.auth0.com/.well-known/openid-configuration",
        json={"jwks_uri": "https://tenant.eu.auth0.com/.well-known/jwks"},
    )
    mocker.patch.object(jwt.PyJWKClient, "fetch_data", return_value=oidc_issuer.jwks)
    token = oidc_issuer.sign_token(aud="https://api.flagsmith.com")

    # When
    result = exchange_oidc_token(token)

    # Then
    access_token_claims = decode_access_token(result.access_token)
    assert access_token_claims["trust_relationship_id"] == trust_relationship.id


def test_exchange_oidc_token__unknown_issuer__raises_no_match(
    oidc_issuer: OIDCIssuerStub,
    github_trust_relationship: TrustRelationship,
    log: StructuredLogCapture,
) -> None:
    # Given
    token = oidc_issuer.sign_token(
        iss="https://other.example.com",
        aud="https://github.com/Flagsmith",
        repository="Flagsmith/flagsmith",
    )

    # When / Then
    with pytest.raises(NoMatchingTrustRelationshipError):
        exchange_oidc_token(token)
    assert log.has("token.rejected", reason="unknown_issuer")


def test_exchange_oidc_token__audience_mismatch__raises_no_match(
    oidc_issuer: OIDCIssuerStub,
    github_trust_relationship: TrustRelationship,
) -> None:
    # Given
    token = oidc_issuer.sign_token(
        aud="https://github.com/SomeoneElse",
        repository="Flagsmith/flagsmith",
    )

    # When / Then
    with pytest.raises(NoMatchingTrustRelationshipError):
        exchange_oidc_token(token)


def test_exchange_oidc_token__no_audience__raises_no_match(
    oidc_issuer: OIDCIssuerStub,
    github_trust_relationship: TrustRelationship,
) -> None:
    # Given
    token = oidc_issuer.sign_token(repository="Flagsmith/flagsmith")

    # When / Then
    with pytest.raises(NoMatchingTrustRelationshipError):
        exchange_oidc_token(token)


def test_exchange_oidc_token__claim_rules_mismatch__raises_no_match(
    oidc_issuer: OIDCIssuerStub,
    github_trust_relationship: TrustRelationship,
    log: StructuredLogCapture,
) -> None:
    # Given
    token = oidc_issuer.sign_token(
        aud="https://github.com/Flagsmith",
        repository="SomeoneElse/repo",
    )

    # When / Then
    with pytest.raises(NoMatchingTrustRelationshipError):
        exchange_oidc_token(token)
    assert log.has("token.rejected", reason="no_match")


def test_exchange_oidc_token__multi_audience_token_matching_multiple__raises_invalid(
    oidc_issuer: OIDCIssuerStub,
    github_trust_relationship: TrustRelationship,
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given: a second trust relationship under a different audience, and a
    # token listing both audiences
    create_trust_relationship(
        organisation_id=organisation.id,
        name="GitHub Actions (CI)",
        issuer="https://token.actions.githubusercontent.com",
        audience="flagsmith-ci",
        is_admin=True,
        claim_rules=[],
    )
    token = oidc_issuer.sign_token(
        aud=["https://github.com/Flagsmith", "flagsmith-ci"],
        repository="Flagsmith/flagsmith",
    )

    # When / Then
    with pytest.raises(InvalidTokenError):
        exchange_oidc_token(token)
    assert log.has("token.rejected", reason="ambiguous")


def test_exchange_oidc_token__expired_token__raises_invalid(
    oidc_issuer: OIDCIssuerStub,
    github_trust_relationship: TrustRelationship,
    log: StructuredLogCapture,
) -> None:
    # Given
    token = oidc_issuer.sign_token(
        expires_in_seconds=-60,
        aud="https://github.com/Flagsmith",
        repository="Flagsmith/flagsmith",
    )

    # When / Then
    with pytest.raises(InvalidTokenError):
        exchange_oidc_token(token)
    assert log.has("token.rejected", reason="verification_failed")


def test_exchange_oidc_token__wrong_signing_key__raises_invalid(
    oidc_issuer: OIDCIssuerStub,
    github_trust_relationship: TrustRelationship,
    log: StructuredLogCapture,
) -> None:
    # Given: a token signed by an impostor with the same issuer and key id
    impostor = OIDCIssuerStub("https://token.actions.githubusercontent.com")
    token = impostor.sign_token(
        aud="https://github.com/Flagsmith",
        repository="Flagsmith/flagsmith",
    )

    # When / Then
    with pytest.raises(InvalidTokenError):
        exchange_oidc_token(token)
    assert log.has("token.rejected", reason="verification_failed")


def test_exchange_oidc_token__malformed_token__raises_invalid(
    github_trust_relationship: TrustRelationship,
    log: StructuredLogCapture,
) -> None:
    # Given
    token = "not-a-jwt"

    # When / Then
    with pytest.raises(InvalidTokenError):
        exchange_oidc_token(token)
    assert log.has("token.rejected", reason="malformed")


def test_exchange_oidc_token__symmetric_algorithm__raises_invalid(
    github_trust_relationship: TrustRelationship,
    log: StructuredLogCapture,
) -> None:
    # Given
    token = jwt.encode(
        {
            "iss": "https://token.actions.githubusercontent.com",
            "aud": "https://github.com/Flagsmith",
            "repository": "Flagsmith/flagsmith",
        },
        "some-secret",
        algorithm="HS256",
    )

    # When / Then
    with pytest.raises(InvalidTokenError):
        exchange_oidc_token(token)
    assert log.has("token.rejected", reason="disallowed_algorithm")


def test_exchange_oidc_token__unknown_signing_key_id__raises_invalid(
    oidc_issuer: OIDCIssuerStub,
    github_trust_relationship: TrustRelationship,
    log: StructuredLogCapture,
) -> None:
    # Given
    # a token whose key id is absent from the issuer's JWKS
    impostor = OIDCIssuerStub("https://token.actions.githubusercontent.com")
    impostor.KEY_ID = "unknown-key"
    token = impostor.sign_token(
        aud="https://github.com/Flagsmith",
        repository="Flagsmith/flagsmith",
    )

    # When / Then
    with pytest.raises(InvalidTokenError):
        exchange_oidc_token(token)
    assert log.has("token.rejected", reason="signing_key_not_found")
