import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet
from django.conf import settings


def _warehouse_credentials_fernet() -> Fernet:
    """The cipher for warehouse credentials, keyed on
    WAREHOUSE_CREDENTIALS_SECRET. The key is the SHA-256 of the secret, so any
    service holding the same secret builds the same cipher and can read what
    another encrypted."""
    secret: str = settings.WAREHOUSE_CREDENTIALS_SECRET
    digest = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_warehouse_credentials(value: Any) -> str:
    return _warehouse_credentials_fernet().encrypt(json.dumps(value).encode()).decode()


def decrypt_warehouse_credentials(token: str) -> Any:
    """Raises ``cryptography.fernet.InvalidToken`` when the token was made
    under a different secret."""
    return json.loads(_warehouse_credentials_fernet().decrypt(token.encode()))
