from typing import Optional

import jwt
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

from api_keys.user import APIKeyUser
from trust_relationships.models import TrustRelationship
from trust_relationships.services import decode_access_token


class TrustRelationshipTokenAuthentication(BaseAuthentication):
    """Authenticate short-lived access tokens minted by the OIDC exchange.

    Resolves the token to the trust relationship's backing master API key,
    so the request authenticates as an `APIKeyUser` and revocation or role
    changes on the trust relationship apply to outstanding tokens.
    """

    def authenticate(self, request: Request) -> Optional[tuple[APIKeyUser, None]]:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.removeprefix("Bearer ").strip()
        try:
            claims = decode_access_token(token)
        except jwt.InvalidTokenError:
            # Not one of ours; let other authenticators have a go.
            return None

        try:
            trust_relationship = TrustRelationship.objects.select_related(
                "master_api_key"
            ).get(id=claims["trust_relationship_id"])
        except TrustRelationship.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                "Trust relationship no longer exists."
            )

        master_api_key = trust_relationship.master_api_key
        if master_api_key.revoked or master_api_key.has_expired:
            raise exceptions.AuthenticationFailed("Trust relationship is revoked.")

        return APIKeyUser(master_api_key), None
