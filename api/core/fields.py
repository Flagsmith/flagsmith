import json
from typing import Any

import structlog
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

logger = structlog.get_logger("core")


def _get_fernet() -> MultiFernet:
    if not settings.CREDENTIALS_ENCRYPTION_KEYS:
        raise ImproperlyConfigured(
            "CREDENTIALS_ENCRYPTION_KEYS must be set to store encrypted fields."
        )
    return MultiFernet([Fernet(key) for key in settings.CREDENTIALS_ENCRYPTION_KEYS])


class EncryptedJSONField(models.TextField[Any, Any]):
    """A JSON value stored Fernet-encrypted in a text column; a value whose
    key left the ring loads as None rather than raising."""

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
        except (InvalidToken, ImproperlyConfigured, ValueError):
            logger.warning("encrypted_field.decrypt_failed", exc_info=True)
            return None
        return json.loads(plaintext)

    def get_lookup(self, lookup_name: str) -> Any:
        if lookup_name != "isnull":
            raise NotImplementedError(
                "EncryptedJSONField only supports isnull lookups."
            )
        return super().get_lookup(lookup_name)
