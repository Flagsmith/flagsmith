import errno
import http.client
import ipaddress
import socket
import ssl
from collections.abc import Iterator

import requests

# RFC 6598 carrier-grade NAT; not caught by ipaddress.is_private.
_SHARED_ADDRESS_SPACE = ipaddress.ip_network("100.64.0.0/10")

# OpenSSL X509_V_ERR_* verification results, named as Node.js reports them.
_CERT_VERIFY_ERROR_CODES = {
    2: "UNABLE_TO_GET_ISSUER_CERT",
    3: "UNABLE_TO_GET_CRL",
    4: "UNABLE_TO_DECRYPT_CERT_SIGNATURE",
    5: "UNABLE_TO_DECRYPT_CRL_SIGNATURE",
    6: "UNABLE_TO_DECODE_ISSUER_PUBLIC_KEY",
    7: "CERT_SIGNATURE_FAILURE",
    8: "CRL_SIGNATURE_FAILURE",
    9: "CERT_NOT_YET_VALID",
    10: "CERT_HAS_EXPIRED",
    11: "CRL_NOT_YET_VALID",
    12: "CRL_HAS_EXPIRED",
    13: "ERROR_IN_CERT_NOT_BEFORE_FIELD",
    14: "ERROR_IN_CERT_NOT_AFTER_FIELD",
    15: "ERROR_IN_CRL_LAST_UPDATE_FIELD",
    16: "ERROR_IN_CRL_NEXT_UPDATE_FIELD",
    18: "DEPTH_ZERO_SELF_SIGNED_CERT",
    19: "SELF_SIGNED_CERT_IN_CHAIN",
    20: "UNABLE_TO_GET_ISSUER_CERT_LOCALLY",
    21: "UNABLE_TO_VERIFY_LEAF_SIGNATURE",
    22: "CERT_CHAIN_TOO_LONG",
    23: "CERT_REVOKED",
    24: "INVALID_CA",
    25: "PATH_LENGTH_EXCEEDED",
    26: "INVALID_PURPOSE",
    27: "CERT_UNTRUSTED",
    28: "CERT_REJECTED",
    62: "ERR_TLS_CERT_ALTNAME_INVALID",  # X509_V_ERR_HOSTNAME_MISMATCH
}


def get_request_error_code(error: requests.RequestException) -> str:
    """Return a POSIX error name, or a Node.js-style TLS error code,
    for a request that failed without an HTTP response."""
    if isinstance(error, requests.exceptions.ConnectTimeout):
        return "ETIMEDOUT"
    if isinstance(error, requests.exceptions.ReadTimeout):
        return "ESOCKETTIMEDOUT"
    for exc in _iter_exception_chain(error):
        if code := _get_exception_error_code(exc):
            return code
    return "UNKNOWN"


def _get_exception_error_code(exc: BaseException) -> str | None:
    # SSL errors subclass OSError, with an OpenSSL-specific errno.
    if isinstance(exc, ssl.SSLCertVerificationError):
        return _CERT_VERIFY_ERROR_CODES.get(exc.verify_code, "EPROTO")
    if isinstance(exc, ssl.SSLError):
        return "EPROTO"
    # gaierror carries an EAI_* errno, not a POSIX one.
    if isinstance(exc, socket.gaierror):
        return "EAI_AGAIN" if exc.errno == socket.EAI_AGAIN else "ENOTFOUND"
    if isinstance(exc, OSError) and exc.errno is not None:
        if name := errno.errorcode.get(exc.errno):
            return name
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
