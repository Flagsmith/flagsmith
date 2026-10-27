import ipaddress
import socket

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

# RFC 6598 carrier-grade NAT; not caught by ipaddress.is_private.
_SHARED_ADDRESS_SPACE = ipaddress.ip_network("100.64.0.0/10")


def resolve_addresses(hostname: str) -> list[IPAddress]:
    """Return the addresses the hostname resolves to, or the address itself for
    an IP literal. Raises ``socket.gaierror`` if it does not resolve."""
    try:
        return [ipaddress.ip_address(hostname)]
    except ValueError:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
        return [ipaddress.ip_address(str(r[4][0]).split("%")[0]) for r in results]


def is_internal_ip(ip: IPAddress, *, include_shared: bool = False) -> bool:
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or (include_shared and ip in _SHARED_ADDRESS_SPACE)
    )


def is_internal_address(
    hostname: str,
    *,
    include_shared: bool = False,
) -> bool:
    """Return True if the hostname is, or resolves to, an internal network
    address: loopback, RFC 1918 private, link-local, reserved, or multicast.
    When *include_shared* is True, also blocks RFC 6598 (100.64.0.0/10).
    Unresolvable hostnames are not considered internal."""
    try:
        ips = resolve_addresses(hostname)
    except socket.gaierror:
        return False

    return any(is_internal_ip(ip, include_shared=include_shared) for ip in ips)
