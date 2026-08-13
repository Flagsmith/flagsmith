import structlog
from django.db import transaction

from api_keys.models import MasterAPIKey
from trust_relationships.models import TrustRelationship
from trust_relationships.types import ClaimRule
from users.models import FFAdminUser

logger = structlog.get_logger("trust_relationships")

BACKING_KEY_NAME_TEMPLATE = "Trust relationship: {name}"


def _backing_key_name(name: str) -> str:
    # The backing key name is display-only; MasterAPIKey.name caps at 50.
    return BACKING_KEY_NAME_TEMPLATE.format(name=name)[:50]


def create_trust_relationship(
    *,
    organisation_id: int,
    name: str,
    issuer: str,
    audience: str,
    is_admin: bool,
    claim_rules: list[ClaimRule],
    created_by: FFAdminUser | None = None,
) -> TrustRelationship:
    with transaction.atomic():
        # The plaintext key is deliberately discarded: the backing key only
        # carries permissions and can never authenticate a request by itself.
        master_api_key, _ = MasterAPIKey.objects.create_key(
            name=_backing_key_name(name),
            organisation_id=organisation_id,
            is_admin=is_admin,
            created_by=created_by,
        )
        trust_relationship: TrustRelationship = TrustRelationship.objects.create(
            organisation_id=organisation_id,
            name=name,
            issuer=issuer,
            audience=audience,
            claim_rules=claim_rules,
            master_api_key=master_api_key,
            created_by=created_by,
        )
    logger.info(
        "created",
        organisation__id=organisation_id,
        trust_relationship__id=trust_relationship.id,
        trust_relationship__issuer=issuer,
    )
    return trust_relationship


def update_trust_relationship(
    *,
    trust_relationship: TrustRelationship,
    name: str,
    issuer: str,
    audience: str,
    is_admin: bool,
    claim_rules: list[ClaimRule],
) -> TrustRelationship:
    with transaction.atomic():
        master_api_key = trust_relationship.master_api_key
        master_api_key.name = _backing_key_name(name)
        # Flipping is_admin back on detaches any RBAC roles via the
        # MasterAPIKey lifecycle hook.
        master_api_key.is_admin = is_admin
        master_api_key.save()

        trust_relationship.name = name
        trust_relationship.issuer = issuer
        trust_relationship.audience = audience
        trust_relationship.claim_rules = claim_rules
        trust_relationship.save()
    logger.info(
        "updated",
        organisation__id=trust_relationship.organisation_id,
        trust_relationship__id=trust_relationship.id,
        trust_relationship__issuer=issuer,
    )
    return trust_relationship


def delete_trust_relationship(*, trust_relationship: TrustRelationship) -> None:
    with transaction.atomic():
        master_api_key = trust_relationship.master_api_key
        master_api_key.revoked = True
        master_api_key.save()
        trust_relationship.delete()
    logger.info(
        "deleted",
        organisation__id=trust_relationship.organisation_id,
        trust_relationship__id=trust_relationship.id,
    )
