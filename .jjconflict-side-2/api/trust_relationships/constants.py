# Asymmetric algorithms accepted on inbound external OIDC tokens.
ALLOWED_SIGNING_ALGORITHMS = ["RS256", "ES256"]

# `token_type` claim value distinguishing minted access tokens from any other
# HS256 JWT signed with SECRET_KEY (e.g. simplejwt sliding cookie tokens).
ACCESS_TOKEN_TYPE = "trust_relationship"

DISCOVERY_TIMEOUT_SECONDS = 5
