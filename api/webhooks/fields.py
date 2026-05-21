import ipaddress
import socket
from urllib.parse import urlparse

from rest_framework import serializers


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

        try:
            ips = [ipaddress.ip_address(hostname)]
        except ValueError:
            # hostname is a name rather than a literal IP — resolve it.
            try:
                results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
                ips = [
                    ipaddress.ip_address(str(r[4][0]).split("%")[0]) for r in results
                ]
            except socket.gaierror:
                # Unresolvable hostname; leave it to the URL validator.
                return

        for ip in ips:
            if (
                ip.is_loopback
                or ip.is_private
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
            ):
                self.fail("internal_address")
