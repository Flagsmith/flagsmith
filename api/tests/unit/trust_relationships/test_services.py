from pytest_structlog import StructuredLogCapture

from api_keys.models import MasterAPIKey
from organisations.models import Organisation
from trust_relationships.models import TrustRelationship
from trust_relationships.services import (
    create_trust_relationship,
    delete_trust_relationship,
    update_trust_relationship,
)
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
    claim_rules = [{"claim": "repository", "values": ["Flagsmith/flagsmith"]}]

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
