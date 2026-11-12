from typing import Any

import structlog
from cryptography.fernet import InvalidToken
from django.db import models

from experimentation.warehouse_credentials import (
    decrypt_warehouse_credentials,
    encrypt_warehouse_credentials,
)

logger = structlog.get_logger("experimentation")


class EncryptedJSONField(models.TextField[Any, Any]):
    """Stores a JSON value as Fernet ciphertext keyed on
    WAREHOUSE_CREDENTIALS_SECRET. Used for a warehouse connection's
    credentials, so the same ciphertext can be handed to the warehouse-delivery
    service."""

    def get_prep_value(self, value: Any) -> str | None:
        if value is None:
            return None
        return encrypt_warehouse_credentials(value)

    def from_db_value(
        self,
        value: str | None,
        expression: object,
        connection: object,
    ) -> Any:
        if value is None:
            return None
        try:
            return decrypt_warehouse_credentials(value)
        except InvalidToken:
            logger.warning("encrypted_field.decrypt_failed", exc_info=True)
            return None

    def get_lookup(self, lookup_name: str) -> Any:
        if lookup_name != "isnull":
            raise NotImplementedError(
                "EncryptedJSONField only supports isnull lookups."
            )
        return super().get_lookup(lookup_name)
