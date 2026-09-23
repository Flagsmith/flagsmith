from dataclasses import dataclass


@dataclass
class TokenExchangeResult:
    access_token: str
    expires_in: int
