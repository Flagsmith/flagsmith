import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import jwt
import structlog
from django.conf import settings
from django.db import transaction

from api_keys.models import MasterAPIKey
from trust_relationships.constants import (
    ACCESS_TOKEN_TYPE,
    ALLOWED_SIGNING_ALGORITHMS,
)
from trust_relationships.dataclasses import TokenExchangeResult
from trust_relationships.exceptions import (
    InvalidTokenError,
    NoMatchingTrustRelationshipError,
)
from trust_relationships.models import TrustRelationship
from trust_relationships.oidc import get_jwks_client, match_claim_rules
from trust_relationships.types import AccessTokenClaims, ClaimRule
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


def mint_access_token(
    trust_relationship: TrustRelationship,
    *,
    sub: str,
) -> TokenExchangeResult:
    """Mint a short-lived HS256 access token bound to a trust relationship."""
    now = datetime.now(tz=timezone.utc)
    expires_in: int = settings.TRUST_RELATIONSHIP_ACCESS_TOKEN_LIFETIME_SECONDS
    access_token = jwt.encode(
        {
            "token_type": ACCESS_TOKEN_TYPE,
            "jti": uuid.uuid4().hex,
            "sub": sub,
            "trust_relationship_id": trust_relationship.id,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return TokenExchangeResult(access_token=access_token, expires_in=expires_in)


def decode_access_token(token: str) -> AccessTokenClaims:
    """Decode and verify a minted access token.

    Raises `jwt.InvalidTokenError` for any token not minted by
    `mint_access_token`, including other HS256 JWTs signed with SECRET_KEY
    (identified via the `token_type` claim).
    """
    claims: dict[str, Any] = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={"require": ["exp", "iat", "jti"]},
    )
    if claims.get("token_type") != ACCESS_TOKEN_TYPE:
        raise jwt.InvalidTokenError("Not a trust relationship access token.")
    if "trust_relationship_id" not in claims:
        raise jwt.InvalidTokenError("Missing trust_relationship_id claim.")
    return cast(AccessTokenClaims, claims)


def exchange_oidc_token(token: str) -> TokenExchangeResult:
    """Exchange an external OIDC token for a short-lived access token.

    The external token's issuer, audience and claims are checked against the
    configured trust relationships; exactly one must match.
    """
    try:
        header = jwt.get_unverified_header(token)
        unverified_claims = jwt.decode(token, options={"verify_signature": False})
    except jwt.InvalidTokenError as exc:
        logger.info("token.rejected", reason="malformed", token__issuer=None)
        raise InvalidTokenError("Token is not a valid JWT.") from exc

    if header.get("alg") not in ALLOWED_SIGNING_ALGORITHMS:
        logger.info("token.rejected", reason="disallowed_algorithm", token__issuer=None)
        raise InvalidTokenError("Token signing algorithm is not allowed.")

    # Preserve the exact `iss` for the lookup: OIDC requires exact string
    # matching, and issuers such as Auth0 legitimately end in a slash.
    issuer = str(unverified_claims.get("iss", ""))
    candidates = list(
        TrustRelationship.objects.filter(issuer=issuer).select_related("master_api_key")
    )
    if not candidates:
        logger.info("token.rejected", reason="unknown_issuer", token__issuer=issuer)
        raise NoMatchingTrustRelationshipError()

    jwks_client = get_jwks_client(issuer)
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=ALLOWED_SIGNING_ALGORITHMS,
            options={"verify_aud": False, "require": ["exp", "iat"]},
        )
    except jwt.PyJWKClientError as exc:
        logger.info(
            "token.rejected", reason="signing_key_not_found", token__issuer=issuer
        )
        raise InvalidTokenError("Unable to resolve issuer signing keys.") from exc
    except jwt.InvalidTokenError as exc:
        logger.info(
            "token.rejected", reason="verification_failed", token__issuer=issuer
        )
        raise InvalidTokenError("Token validation failed.") from exc

    audiences = claims.get("aud") or []
    if not isinstance(audiences, list):
        audiences = [audiences]
    matched = [
        trust_relationship
        for trust_relationship in candidates
        if trust_relationship.audience in audiences
        and match_claim_rules(claims, trust_relationship.claim_rules)
    ]

    if not matched:
        logger.info("token.rejected", reason="no_match", token__issuer=issuer)
        raise NoMatchingTrustRelationshipError()
    if len(matched) > 1:
        # Only reachable with a multi-audience token (RFC 7519 allows `aud`
        # to be an array)
        logger.info("token.rejected", reason="ambiguous", token__issuer=issuer)
        raise InvalidTokenError("Token audience matches multiple trust relationships.")

    trust_relationship = matched[0]
    result = mint_access_token(trust_relationship, sub=str(claims.get("sub", "")))
    logger.info(
        "token.exchanged",
        organisation__id=trust_relationship.organisation_id,
        trust_relationship__id=trust_relationship.id,
        token__sub=str(claims.get("sub", "")),
    )
    return result
