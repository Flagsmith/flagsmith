from typing import TypeVar

from django.db import models

from core.validators import validate_http_url_scheme, validate_no_internal_address

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
