from fnmatch import fnmatchcase
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

import jwt
import requests

from trust_relationships.constants import DISCOVERY_TIMEOUT_SECONDS
from trust_relationships.exceptions import InvalidTokenError


@lru_cache(maxsize=128)
def get_jwks_client(issuer: str) -> jwt.PyJWKClient:
    """Resolve an issuer's JWKS endpoint via OIDC discovery.

    Only successful lookups are cached; the returned client caches fetched
    keys internally.
    """
    try:
        # Strip any trailing slash here so discovery hits
        # `.../.well-known/openid-configuration`, not `...//.well-known/...`.
        base_url = issuer.rstrip("/")
        response = requests.get(
            f"{base_url}/.well-known/openid-configuration",
            timeout=DISCOVERY_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        jwks_uri = response.json()["jwks_uri"]
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise InvalidTokenError("Unable to resolve issuer signing keys.") from exc
    if urlparse(jwks_uri).scheme != "https":
        raise InvalidTokenError("Issuer JWKS endpoint must be served over https.")
    return jwt.PyJWKClient(jwks_uri, cache_keys=True)


def match_claim_rules(
    claims: dict[str, Any],
    claim_rules: list[dict[str, Any]],
) -> bool:
    """Check token claims against a trust relationship's claim rules.

    Every rule must match. A rule matches when the claim is present and any
    of the rule's values matches it; values support `*` glob wildcards.
    List-valued claims match if any element matches.
    """
    for rule in claim_rules:
        claim_value = claims.get(rule["claim"])
        if claim_value is None:
            return False
        candidates = claim_value if isinstance(claim_value, list) else [claim_value]
        if not any(
            fnmatchcase(str(candidate), pattern)
            for candidate in candidates
            for pattern in rule["values"]
        ):
            return False
    return True
