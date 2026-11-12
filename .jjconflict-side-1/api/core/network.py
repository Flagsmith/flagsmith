import ipaddress
import socket

# RFC 6598 carrier-grade NAT; not caught by ipaddress.is_private.
_SHARED_ADDRESS_SPACE = ipaddress.ip_network("100.64.0.0/10")


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
        ips = [ipaddress.ip_address(hostname)]
    except ValueError:
        try:
            results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
            ips = [ipaddress.ip_address(str(r[4][0]).split("%")[0]) for r in results]
        except socket.gaierror:
            return False

    return any(
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or (include_shared and ip in _SHARED_ADDRESS_SPACE)
        for ip in ips
    )
