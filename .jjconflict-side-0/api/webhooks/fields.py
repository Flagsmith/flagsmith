from typing import Any

from rest_framework import serializers

from core.validators import validate_http_url_scheme, validate_no_internal_address


class NoSSRFURLField(serializers.URLField):
    """
    A URL field that only allows http(s) URLs and rejects URLs resolving to
    internal network addresses, preventing Server-Side Request Forgery
    (SSRF) attacks.

    For serialisers not backed by a model. Model-backed serialisers get the
    same validation from `core.fields.NoSSRFURLField`.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.validators += [validate_http_url_scheme, validate_no_internal_address]
