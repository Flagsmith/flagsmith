from urllib.parse import urlparse

from rest_framework import serializers

from core.network import is_internal_address


class NoSSRFURLField(serializers.URLField):
    """
    A URL field that rejects URLs resolving to internal network addresses,
    preventing Server-Side Request Forgery (SSRF) attacks.

    Blocks loopback (127.0.0.0/8, ::1), RFC 1918 private ranges
    (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), link-local
    (169.254.0.0/16, fe80::/10), and other reserved/multicast ranges.
    Hostnames are resolved to their IP address before checking.
    """

    default_error_messages = {
        **serializers.URLField.default_error_messages,
        "internal_address": (
            "Webhook URLs must not target internal or private network addresses."
        ),
    }

    def run_validators(self, value: str) -> None:
        super().run_validators(value)

        hostname = urlparse(value).hostname or ""
        if is_internal_address(hostname):
            self.fail("internal_address")
