import ipaddress
import socket


def is_internal_address(hostname: str) -> bool:
    """Return True if the hostname is, or resolves to, an internal network
    address: loopback, RFC 1918 private, link-local, reserved, or multicast.
    Unresolvable hostnames are not considered internal."""
    try:
        ips = [ipaddress.ip_address(hostname)]
    except ValueError:
        # hostname is a name rather than a literal IP — resolve it.
        try:
            results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
            ips = [ipaddress.ip_address(str(r[4][0]).split("%")[0]) for r in results]
        except socket.gaierror:
            return False

    _SHARED_ADDRESS_SPACE = ipaddress.ip_network("100.64.0.0/10")

    return any(
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip in _SHARED_ADDRESS_SPACE
        for ip in ips
    )
