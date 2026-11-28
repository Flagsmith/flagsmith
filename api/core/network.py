import errno
import http.client
import ipaddress
import socket
import ssl
from collections.abc import Iterator

import requests

# RFC 6598 carrier-grade NAT; not caught by ipaddress.is_private.
_SHARED_ADDRESS_SPACE = ipaddress.ip_network("100.64.0.0/10")

# OpenSSL 3+ certificate verification results, from `include/openssl/x509_vfy.h`.
# Python exposes the numeric `verify_code`, but not the constant names.
_CERT_VERIFY_ERROR_NAMES = {
    2: "X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT",
    3: "X509_V_ERR_UNABLE_TO_GET_CRL",
    4: "X509_V_ERR_UNABLE_TO_DECRYPT_CERT_SIGNATURE",
    5: "X509_V_ERR_UNABLE_TO_DECRYPT_CRL_SIGNATURE",
    6: "X509_V_ERR_UNABLE_TO_DECODE_ISSUER_PUBLIC_KEY",
    7: "X509_V_ERR_CERT_SIGNATURE_FAILURE",
    8: "X509_V_ERR_CRL_SIGNATURE_FAILURE",
    9: "X509_V_ERR_CERT_NOT_YET_VALID",
    10: "X509_V_ERR_CERT_HAS_EXPIRED",
    11: "X509_V_ERR_CRL_NOT_YET_VALID",
    12: "X509_V_ERR_CRL_HAS_EXPIRED",
    13: "X509_V_ERR_ERROR_IN_CERT_NOT_BEFORE_FIELD",
    14: "X509_V_ERR_ERROR_IN_CERT_NOT_AFTER_FIELD",
    15: "X509_V_ERR_ERROR_IN_CRL_LAST_UPDATE_FIELD",
    16: "X509_V_ERR_ERROR_IN_CRL_NEXT_UPDATE_FIELD",
    18: "X509_V_ERR_DEPTH_ZERO_SELF_SIGNED_CERT",
    19: "X509_V_ERR_SELF_SIGNED_CERT_IN_CHAIN",
    20: "X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY",
    21: "X509_V_ERR_UNABLE_TO_VERIFY_LEAF_SIGNATURE",
    22: "X509_V_ERR_CERT_CHAIN_TOO_LONG",
    23: "X509_V_ERR_CERT_REVOKED",
    24: "X509_V_ERR_NO_ISSUER_PUBLIC_KEY",
    25: "X509_V_ERR_PATH_LENGTH_EXCEEDED",
    26: "X509_V_ERR_INVALID_PURPOSE",
    27: "X509_V_ERR_CERT_UNTRUSTED",
    28: "X509_V_ERR_CERT_REJECTED",
    62: "X509_V_ERR_HOSTNAME_MISMATCH",
    64: "X509_V_ERR_IP_ADDRESS_MISMATCH",
    66: "X509_V_ERR_EE_KEY_TOO_SMALL",
    67: "X509_V_ERR_CA_KEY_TOO_SMALL",
    68: "X509_V_ERR_CA_MD_TOO_WEAK",
    79: "X509_V_ERR_INVALID_CA",
}

# getaddrinfo() returns EAI_* codes, which don't overlap with errno.
_GETADDRINFO_ERROR_NAMES = {
    getattr(socket, name): name for name in dir(socket) if name.startswith("EAI_")
}


def get_request_error_code(error: requests.RequestException) -> str | None:
    """Return the POSIX error name, or the OpenSSL certificate verification
    error name, for a request that failed without an HTTP response."""
    if isinstance(error, requests.exceptions.Timeout):
        return "ETIMEDOUT"
    for exc in _iter_exception_chain(error):
        if code := _get_exception_error_code(exc):
            return code
    return None


def _get_exception_error_code(exc: BaseException) -> str | None:
    # SSL errors subclass OSError, with an OpenSSL-specific errno.
    if isinstance(exc, ssl.SSLCertVerificationError):
        return _CERT_VERIFY_ERROR_NAMES.get(exc.verify_code, "EPROTO")
    if isinstance(exc, ssl.SSLError):
        return "EPROTO"
    if isinstance(exc, socket.gaierror) and exc.errno is not None:
        return _GETADDRINFO_ERROR_NAMES.get(exc.errno)
    if isinstance(exc, OSError) and exc.errno is not None:
        if name := errno.errorcode.get(exc.errno):
            return name
    # A socket timeout, e.g. connecting to a proxy, without an errno.
    if isinstance(exc, TimeoutError):
        return "ETIMEDOUT"
    # e.g. `RemoteDisconnected`: the peer closed without responding.
    if isinstance(exc, ConnectionResetError):
        return "ECONNRESET"
    # The peer responded with something other than HTTP.
    if isinstance(exc, http.client.HTTPException):
        return "EPROTO"
    return None


def _iter_exception_chain(error: BaseException) -> Iterator[BaseException]:
    # requests and urllib3 wrap the underlying error in `reason` and
    # `original_error` as well as in the standard `__cause__`/`__context__`.
    seen: set[int] = set()
    pending: list[BaseException] = [error]
    while pending:
        exc = pending.pop(0)
        if id(exc) in seen:
            continue
        seen.add(id(exc))
        yield exc
        for attr in ("reason", "original_error", "__cause__", "__context__"):
            linked = getattr(exc, attr, None)
            if isinstance(linked, BaseException):
                pending.append(linked)
        pending.extend(arg for arg in exc.args if isinstance(arg, BaseException))


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
