import datetime

import jwt
import pytest
from django.conf import settings
from freezegun import freeze_time
from pytest_structlog import StructuredLogCapture

from api_keys.models import MasterAPIKey
from organisations.models import Organisation
from trust_relationships.models import TrustRelationship
from trust_relationships.services import (
    create_trust_relationship,
    decode_access_token,
    delete_trust_relationship,
    mint_access_token,
    update_trust_relationship,
)
from trust_relationships.types import ClaimRule
from users.models import FFAdminUser


def test_create_trust_relationship__valid_data__creates_hidden_backing_key(
    organisation: Organisation,
    admin_user: FFAdminUser,
    log: StructuredLogCapture,
) -> None:
    # Given
    name = "GitHub Actions"
    issuer = "https://token.actions.githubusercontent.com"
    audience = "https://github.com/Flagsmith"
    claim_rules: list[ClaimRule] = [
        {"claim": "repository", "values": ["Flagsmith/flagsmith"]}
    ]

    # When
    trust_relationship = create_trust_relationship(
        organisation_id=organisation.id,
        name=name,
        issuer=issuer,
        audience=audience,
        is_admin=True,
        claim_rules=claim_rules,
        created_by=admin_user,
    )

    # Then
    backing_key = trust_relationship.master_api_key
    assert backing_key.organisation_id == organisation.id
    assert backing_key.is_admin is True
    assert backing_key.created_by == admin_user
    assert backing_key.name == "Trust relationship: GitHub Actions"
    assert backing_key.hashed_key
    assert backing_key.revoked is False
    assert log.has(
        "created",
        organisation__id=organisation.id,
        trust_relationship__id=trust_relationship.id,
        trust_relationship__issuer="https://token.actions.githubusercontent.com",
    )


def test_update_trust_relationship__new_values__syncs_backing_key(
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given
    trust_relationship = create_trust_relationship(
        organisation_id=organisation.id,
        name="GitHub Actions",
        issuer="https://token.actions.githubusercontent.com",
        audience="https://github.com/Flagsmith",
        is_admin=True,
        claim_rules=[],
    )

    # When
    updated = update_trust_relationship(
        trust_relationship=trust_relationship,
        name="GitHub Actions (prod)",
        issuer="https://token.actions.githubusercontent.com",
        audience="flagsmith-prod",
        is_admin=False,
        claim_rules=[{"claim": "environment", "values": ["production"]}],
    )

    # Then
    assert updated.name == "GitHub Actions (prod)"
    assert updated.audience == "flagsmith-prod"
    assert updated.claim_rules == [{"claim": "environment", "values": ["production"]}]
    backing_key = updated.master_api_key
    assert backing_key.name == "Trust relationship: GitHub Actions (prod)"
    assert backing_key.is_admin is False
    assert log.has(
        "updated",
        organisation__id=organisation.id,
        trust_relationship__id=trust_relationship.id,
        trust_relationship__issuer="https://token.actions.githubusercontent.com",
    )


def test_delete_trust_relationship__existing__revokes_backing_key(
    organisation: Organisation,
    log: StructuredLogCapture,
) -> None:
    # Given
    trust_relationship = create_trust_relationship(
        organisation_id=organisation.id,
        name="GitHub Actions",
        issuer="https://token.actions.githubusercontent.com",
        audience="https://github.com/Flagsmith",
        is_admin=True,
        claim_rules=[],
    )
    trust_relationship_id = trust_relationship.id
    backing_key_id = trust_relationship.master_api_key_id

    # When
    delete_trust_relationship(trust_relationship=trust_relationship)

    # Then
    assert not TrustRelationship.objects.filter(id=trust_relationship_id).exists()
    backing_key = MasterAPIKey.objects.get(id=backing_key_id)
    assert backing_key.revoked is True
    assert log.has(
        "deleted",
        organisation__id=organisation.id,
        trust_relationship__id=trust_relationship_id,
    )


def test_mint_access_token__valid_input__round_trips(
    github_trust_relationship: TrustRelationship,
) -> None:
    # Given
    sub = "repo:Flagsmith/flagsmith:ref:refs/heads/main"

    # When
    result = mint_access_token(github_trust_relationship, sub=sub)

    # Then
    assert result.expires_in == 3600
    claims = decode_access_token(result.access_token)
    assert claims["trust_relationship_id"] == github_trust_relationship.id
    assert claims["sub"] == "repo:Flagsmith/flagsmith:ref:refs/heads/main"
    assert claims["jti"]


def test_decode_access_token__foreign_hs256_token__raises_invalid() -> None:
    # Given: an HS256 token signed with SECRET_KEY but minted elsewhere
    # (e.g. a simplejwt sliding cookie token)
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    token = jwt.encode(
        {
            "jti": "abc",
            "iat": now,
            "exp": now + datetime.timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    # When / Then
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_decode_access_token__expired_token__raises_invalid(
    github_trust_relationship: TrustRelationship,
) -> None:
    # Given
    with freeze_time("2026-07-18T10:00:00Z"):
        result = mint_access_token(github_trust_relationship, sub="test")

    # When / Then
    with freeze_time("2026-07-18T12:00:00Z"):
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(result.access_token)


def test_decode_access_token__missing_trust_relationship_id__raises_invalid() -> None:
    # Given
    # a token with the right type but no trust_relationship_id
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    token = jwt.encode(
        {
            "token_type": "trust_relationship",
            "jti": "abc",
            "iat": now,
            "exp": now + datetime.timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    # When / Then
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)
