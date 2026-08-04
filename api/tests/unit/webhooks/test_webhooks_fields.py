import socket
from unittest import mock

import pytest
from rest_framework.exceptions import ValidationError

from webhooks.fields import NoSSRFURLField


@pytest.fixture()
def field() -> NoSSRFURLField:
    return NoSSRFURLField()


@pytest.mark.parametrize(
    "url,label",
    [
        ("http://127.0.0.1/hook", "loopback IPv4"),
        ("http://127.0.0.2/hook", "loopback IPv4 (non-first)"),
        ("http://[::1]/hook", "loopback IPv6"),
        ("http://10.0.0.1/hook", "RFC1918 10.0.0.0/8"),
        ("http://10.255.255.255/hook", "RFC1918 10.0.0.0/8 boundary"),
        ("http://172.16.0.1/hook", "RFC1918 172.16.0.0/12"),
        ("http://172.31.255.255/hook", "RFC1918 172.16.0.0/12 boundary"),
        ("http://192.168.0.1/hook", "RFC1918 192.168.0.0/16"),
        ("http://192.168.255.255/hook", "RFC1918 192.168.0.0/16 boundary"),
        ("http://169.254.1.1/hook", "link-local IPv4"),
        ("http://[fe80::1]/hook", "link-local IPv6"),
        ("http://224.0.0.1/hook", "multicast"),
        ("http://240.0.0.1/hook", "reserved"),
    ],
)
def test_no_ssrf_url_field__internal_ip__raises_validation_error(  # noqa: FT004
    field: NoSSRFURLField,
    url: str,
    label: str,
) -> None:
    # Given / When / Then
    with pytest.raises(ValidationError) as exc_info:
        field.run_validation(url)

    assert "internal_address" in str(exc_info.value.detail)


def test_no_ssrf_url_field__localhost_hostname__raises_validation_error(
    field: NoSSRFURLField,
) -> None:
    # Given — localhost resolves to 127.0.0.1
    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        field.run_validation("http://localhost/hook")

    assert "internal_address" in str(exc_info.value.detail)


def test_no_ssrf_url_field__hostname_resolving_to_private_ip__raises_validation_error(
    field: NoSSRFURLField,
) -> None:
    # Given — a hostname that resolves to an RFC1918 address
    with mock.patch(
        "core.network.socket.getaddrinfo",
        return_value=[(socket.AF_INET, None, None, None, ("192.168.1.100", 0))],
    ):
        # When / Then
        with pytest.raises(ValidationError) as exc_info:
            field.run_validation("http://internal.example.com/hook")

    assert "internal_address" in str(exc_info.value.detail)


def test_no_ssrf_url_field__hostname_resolving_to_private_ipv6__raises_validation_error(
    field: NoSSRFURLField,
) -> None:
    # Given — an AAAA-only hostname resolving to a private IPv6 address
    with mock.patch(
        "core.network.socket.getaddrinfo",
        return_value=[(socket.AF_INET6, None, None, None, ("fc00::1", 0, 0, 0))],
    ):
        # When / Then
        with pytest.raises(ValidationError) as exc_info:
            field.run_validation("http://internal-v6.example.com/hook")

    assert "internal_address" in str(exc_info.value.detail)


@pytest.mark.parametrize(
    "url,label",
    [
        ("https://example.com/hook", "public hostname"),
        ("https://hooks.example.org/path?foo=bar", "public hostname with path"),
        ("http://8.8.8.8/hook", "public IPv4"),
    ],
)
def test_no_ssrf_url_field__public_address__returns_value(
    field: NoSSRFURLField,
    url: str,
    label: str,
) -> None:
    # Given / When
    result = field.run_validation(url)

    # Then
    assert result == url


def test_no_ssrf_url_field__unresolvable_hostname__returns_value(
    field: NoSSRFURLField,
) -> None:
    # Given — the hostname cannot be resolved; URL format is still valid
    with mock.patch(
        "core.network.socket.getaddrinfo",
        side_effect=socket.gaierror,
    ):
        # When
        result = field.run_validation("https://unresolvable.example.com/hook")

    # Then
    assert result == "https://unresolvable.example.com/hook"
