from typing import TypedDict


class ClaimRule(TypedDict):
    """A single constraint an exchanged token's claims must satisfy.

    A token is accepted only if its ``claim`` holds one of ``values``.
    """

    claim: str
    values: list[str]


class AccessTokenClaims(TypedDict):
    """Claims carried by a minted trust relationship access token."""

    token_type: str
    jti: str
    sub: str
    trust_relationship_id: int
    iat: int
    exp: int
