from urllib.parse import urlparse

from django.core.exceptions import ValidationError

from core.network import is_internal_address

ALLOWED_URL_SCHEMES = ("http", "https")


def validate_http_url_scheme(value: str) -> None:
    """
    Restrict a URL to http(s). Django's `URLValidator` also allows ftp(s).

    Deliberately not a `URLValidator` subclass: DRF drops any `URLValidator`
    it copies from a model field onto a `ModelSerializer` field, replacing it
    with its own scheme-permissive one.
    """
    if urlparse(value).scheme not in ALLOWED_URL_SCHEMES:
        raise ValidationError("Enter a valid http(s) URL.", code="invalid")


def validate_no_internal_address(value: str) -> None:
    """
    Reject URLs that target, or resolve to, an internal or private network
    address, preventing Server-Side Request Forgery (SSRF).
    """
    if is_internal_address(urlparse(value).hostname or ""):
        raise ValidationError(
            "URLs must not target internal or private network addresses.",
            code="internal_address",
        )
