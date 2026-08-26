import json
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from flag_engine.segments.types import ConditionOperator


def generate_segment_data(
    segment_name: str,
    project_id: int,
    condition_tuples: list[tuple[str, ConditionOperator, str]],
) -> dict[str, Any]:
    return {
        "name": segment_name,
        "project": project_id,
        "rules": [
            {
                "type": "ALL",
                "rules": [
                    {
                        "type": "ANY",
                        "rules": [],
                        "conditions": [
                            {
                                "property": condition_tuple[0],
                                "operator": condition_tuple[1],
                                "value": condition_tuple[2],
                            }
                            for condition_tuple in condition_tuples
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }


class OIDCIssuerStub:
    """An RSA keypair posing as an OIDC issuer: signs tokens and serves the
    matching JWKS in tests.
    """

    KEY_ID = "test-key"

    def __init__(self, issuer: str) -> None:
        self.issuer = issuer
        self._private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )

    @property
    def jwks(self) -> dict[str, Any]:
        jwk = json.loads(
            jwt.algorithms.RSAAlgorithm.to_jwk(self._private_key.public_key())
        )
        jwk["kid"] = self.KEY_ID
        return {"keys": [jwk]}

    def sign_token(self, expires_in_seconds: int = 300, **claims: Any) -> str:
        now = datetime.now(tz=timezone.utc)
        payload: dict[str, Any] = {
            "iss": self.issuer,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in_seconds),
            **claims,
        }
        return jwt.encode(
            payload,
            self._private_key,
            algorithm="RS256",
            headers={"kid": self.KEY_ID},
        )
