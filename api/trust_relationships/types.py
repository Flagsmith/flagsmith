from typing import TypedDict


class AccessTokenClaims(TypedDict):
    """Claims carried by a minted trust relationship access token."""

    token_type: str
    jti: str
    sub: str
    trust_relationship_id: int
    iat: int
    exp: int
