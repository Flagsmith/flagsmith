import logging
import secrets
from urllib.parse import urlencode

import requests
from django.core.cache import cache

from custom_auth.oauth.exceptions import OIDCError

logger = logging.getLogger(__name__)

OIDC_STATE_CACHE_PREFIX = "oidc_state_"
OIDC_STATE_TIMEOUT = 300  # 5 minutes


class OIDCProvider:
    """Handles OIDC authentication flow against a discovery-based provider (e.g. Keycloak)."""

    def __init__(self, provider_url: str, client_id: str, client_secret: str) -> None:
        self.provider_url = provider_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._config: dict = {}

    def _get_discovery_config(self) -> dict:  # type: ignore[type-arg]
        if not self._config:
            discovery_url = f"{self.provider_url}/.well-known/openid-configuration"
            try:
                response = requests.get(discovery_url, timeout=10)
                response.raise_for_status()
                self._config = response.json()
            except requests.RequestException as e:
                raise OIDCError(f"Failed to fetch OIDC discovery document: {e}")
        return self._config

    def get_authorization_url(self, redirect_uri: str) -> str:
        config = self._get_discovery_config()
        auth_endpoint = config.get("authorization_endpoint")
        if not auth_endpoint:
            raise OIDCError("OIDC discovery document missing 'authorization_endpoint'.")

        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        cache.set(
            f"{OIDC_STATE_CACHE_PREFIX}{state}",
            {"nonce": nonce, "redirect_uri": redirect_uri},
            timeout=OIDC_STATE_TIMEOUT,
        )

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
        }
        return f"{auth_endpoint}?{urlencode(params)}"

    def exchange_code_for_user_info(self, code: str, state: str, redirect_uri: str) -> dict:  # type: ignore[type-arg]
        cached = cache.get(f"{OIDC_STATE_CACHE_PREFIX}{state}")
        if not cached:
            raise OIDCError("Invalid or expired OIDC state parameter.")
        cache.delete(f"{OIDC_STATE_CACHE_PREFIX}{state}")

        config = self._get_discovery_config()
        token_endpoint = config.get("token_endpoint")
        if not token_endpoint:
            raise OIDCError("OIDC discovery document missing 'token_endpoint'.")

        token_response = requests.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=10,
        )
        if not token_response.ok:
            raise OIDCError(
                f"Failed to exchange authorization code: {token_response.text}"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise OIDCError("Token response missing 'access_token'.")

        userinfo_endpoint = config.get("userinfo_endpoint")
        if not userinfo_endpoint:
            raise OIDCError("OIDC discovery document missing 'userinfo_endpoint'.")

        userinfo_response = requests.get(
            userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if not userinfo_response.ok:
            raise OIDCError(f"Failed to fetch user info: {userinfo_response.text}")

        userinfo = userinfo_response.json()
        email = userinfo.get("email")
        if not email:
            raise OIDCError("OIDC userinfo response missing 'email' claim.")

        given_name = userinfo.get("given_name", "")
        family_name = userinfo.get("family_name", "")
        if not given_name and not family_name:
            full_name = userinfo.get("name", "")
            parts = full_name.split(" ", 1)
            given_name = parts[0]
            family_name = parts[1] if len(parts) > 1 else ""

        return {
            "email": email,
            "first_name": given_name,
            "last_name": family_name,
        }
