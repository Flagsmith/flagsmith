from typing import TypedDict


class ClaimRule(TypedDict):
    """A single constraint an exchanged token's claims must satisfy.

    A token is accepted only if its ``claim`` holds one of ``values``.
    """

    claim: str
    values: list[str]
