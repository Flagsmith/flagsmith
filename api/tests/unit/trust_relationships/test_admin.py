from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest

from api_keys.models import MasterAPIKey
from organisations.models import Organisation
from trust_relationships.admin import TrustRelationshipAdmin
from trust_relationships.models import TrustRelationship
from trust_relationships.services import create_trust_relationship


def test_delete_model__existing__revokes_backing_key(
    organisation: Organisation,
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
    backing_key_id = trust_relationship.master_api_key_id
    model_admin = TrustRelationshipAdmin(TrustRelationship, AdminSite())

    # When
    model_admin.delete_model(HttpRequest(), trust_relationship)

    # Then
    assert not TrustRelationship.objects.filter(id=trust_relationship.id).exists()
    assert MasterAPIKey.objects.get(id=backing_key_id).revoked is True


def test_delete_queryset__existing__revokes_backing_keys(
    organisation: Organisation,
) -> None:
    # Given
    trust_relationships = [
        create_trust_relationship(
            organisation_id=organisation.id,
            name=f"GitHub Actions {i}",
            issuer=f"https://token.actions.githubusercontent.com/{i}",
            audience="https://github.com/Flagsmith",
            is_admin=True,
            claim_rules=[],
        )
        for i in range(2)
    ]
    backing_key_ids = [
        trust_relationship.master_api_key_id
        for trust_relationship in trust_relationships
    ]
    model_admin = TrustRelationshipAdmin(TrustRelationship, AdminSite())

    # When
    model_admin.delete_queryset(HttpRequest(), TrustRelationship.objects.all())

    # Then
    assert not TrustRelationship.objects.exists()
    assert all(
        MasterAPIKey.objects.get(id=backing_key_id).revoked
        for backing_key_id in backing_key_ids
    )
