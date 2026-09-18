from typing import Any, TypeVar

import structlog
from cryptography.fernet import InvalidToken
from django.db import models

from core.validators import validate_http_url_scheme, validate_no_internal_address
from core.warehouse_credentials import (
    decrypt_warehouse_credentials,
    encrypt_warehouse_credentials,
)

logger = structlog.get_logger("core")

_ST = TypeVar("_ST")
_GT = TypeVar("_GT")


class NoSSRFURLField(models.URLField[_ST, _GT]):
    """
    A URL field restricted to http(s) URLs that do not resolve to internal or
    private network addresses.

    DRF copies these validators onto the `ModelSerializer` field it builds, so
    any serialiser over a model using this field validates the URL on input.
    Use `webhooks.fields.NoSSRFURLField` for serialisers not backed by a model.

    Kept generic so django-stubs can still derive nullability from `null=`;
    subclassing `models.URLField` unparameterised resolves every usage to `Any`.
    """

    default_validators = [
        *models.URLField.default_validators,
        validate_http_url_scheme,
        validate_no_internal_address,
    ]


class EncryptedJSONField(models.TextField[Any, Any]):
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
