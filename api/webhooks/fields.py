from typing import Any
from urllib.parse import urlparse

from django.core.validators import URLValidator
from rest_framework import serializers

from core.network import is_internal_address


class NoSSRFURLField(serializers.URLField):
    """
    A URL field that only allows http(s) URLs and rejects URLs resolving to
    internal network addresses, preventing Server-Side Request Forgery
    (SSRF) attacks.

    Restricts the scheme to http/https, and blocks loopback (127.0.0.0/8,
    ::1), RFC 1918 private ranges (10.0.0.0/8, 172.16.0.0/12,
    192.168.0.0/16), link-local (169.254.0.0/16, fe80::/10), and other
    reserved/multicast ranges. Hostnames are resolved to their IP address
    before checking, so DNS names that resolve to an internal address are
    rejected too.
    """

    default_error_messages = {
        **serializers.URLField.default_error_messages,
        "internal_address": (
            "URLs must not target internal or private network addresses."
        ),
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # The base URLField's validator allows ftp/ftps; replace it so only
        # http/https URLs are accepted.
        self.validators = [
            validator
            for validator in self.validators
            if not isinstance(validator, URLValidator)
        ]
        self.validators.append(
            URLValidator(
                schemes=["http", "https"],
                message=self.error_messages["invalid"],
            )
        )

    def run_validators(self, value: str) -> None:
        super().run_validators(value)

        hostname = urlparse(value).hostname or ""
        if is_internal_address(hostname):
            self.fail("internal_address")
