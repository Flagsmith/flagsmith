import base64
import hashlib
import json
from typing import Any

import structlog
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

logger = structlog.get_logger("core")


def _get_fernet() -> Fernet:
    secret: str = settings.WAREHOUSE_CREDENTIALS_SECRET
    digest = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


class EncryptedJSONField(models.TextField[Any, Any]):
    def get_prep_value(self, value: Any) -> str | None:
        if value is None:
            return None
        return _get_fernet().encrypt(json.dumps(value).encode()).decode()

    def from_db_value(
        self,
        value: str | None,
        expression: object,
        connection: object,
    ) -> Any:
        if value is None:
            return None
        try:
            plaintext = _get_fernet().decrypt(value.encode())
        except InvalidToken:
            logger.warning("encrypted_field.decrypt_failed", exc_info=True)
            return None
        return json.loads(plaintext)

    def get_lookup(self, lookup_name: str) -> Any:
        if lookup_name != "isnull":
            raise NotImplementedError(
                "EncryptedJSONField only supports isnull lookups."
            )
        return super().get_lookup(lookup_name)
