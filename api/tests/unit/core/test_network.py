import errno
import http.client
import socket
import ssl
from typing import TypeVar

import pytest
import requests
from urllib3 import HTTPSConnectionPool
from urllib3.connection import HTTPSConnection
from urllib3.exceptions import (
    ConnectTimeoutError,
    MaxRetryError,
    NameResolutionError,
    NewConnectionError,
    ProtocolError,
)
from urllib3.exceptions import ProxyError as Urllib3ProxyError
from urllib3.exceptions import SSLError as Urllib3SSLError

from core.network import get_request_error_code

_E = TypeVar("_E", bound=BaseException)

# Constructing these doesn't open a connection.
_POOL = HTTPSConnectionPool("example.com")
_CONN = HTTPSConnection("example.com")


def _caused_by(error: _E, cause: BaseException) -> _E:
    error.__cause__ = cause
    return error


def _max_retries(reason: Exception) -> MaxRetryError:
    # How requests' HTTPAdapter receives connection failures from urllib3.
    return MaxRetryError(_POOL, "/", reason=reason)


def _cert_verify_error(verify_code: int) -> ssl.SSLCertVerificationError:
    error = ssl.SSLCertVerificationError(1, "certificate verify failed")
    error.verify_code = verify_code
    return error


@pytest.mark.parametrize(
    "error, expected_code",
    [
        (
            requests.exceptions.ConnectionError(
                _max_retries(
                    _caused_by(
                        NewConnectionError(_CONN, "Failed to establish a connection"),
                        ConnectionRefusedError(errno.ECONNREFUSED, "refused"),
                    )
                )
            ),
            "ECONNREFUSED",
        ),
        (
            requests.exceptions.ConnectionError(
                _max_retries(
                    _caused_by(
                        NewConnectionError(_CONN, "Failed to establish a connection"),
                        OSError(errno.EHOSTUNREACH, "no route to host"),
                    )
                )
            ),
            "EHOSTUNREACH",
        ),
        (
            requests.exceptions.ConnectionError(
                _max_retries(
                    _caused_by(
                        NameResolutionError(
                            "example.com",
                            _CONN,
                            socket.gaierror(socket.EAI_NONAME, "Name not known"),
                        ),
                        socket.gaierror(socket.EAI_NONAME, "Name not known"),
                    )
                )
            ),
            "EAI_NONAME",
        ),
        (
            requests.exceptions.ConnectionError(
                _max_retries(
                    _caused_by(
                        NameResolutionError(
                            "example.com",
                            _CONN,
                            socket.gaierror(socket.EAI_AGAIN, "Temporary failure"),
                        ),
                        socket.gaierror(socket.EAI_AGAIN, "Temporary failure"),
                    )
                )
            ),
            "EAI_AGAIN",
        ),
        (
            requests.exceptions.ConnectionError(
                _max_retries(
                    _caused_by(
                        NameResolutionError(
                            "example.com",
                            _CONN,
                            socket.gaierror(socket.EAI_FAIL, "Non-recoverable"),
                        ),
                        socket.gaierror(socket.EAI_FAIL, "Non-recoverable"),
                    )
                )
            ),
            "EAI_FAIL",
        ),
        (
            requests.exceptions.ConnectionError(
                ProtocolError(
                    "Connection aborted.",
                    ConnectionResetError(errno.ECONNRESET, "reset by peer"),
                )
            ),
            "ECONNRESET",
        ),
        (
            requests.exceptions.ConnectionError(
                ProtocolError(
                    "Connection aborted.",
                    http.client.RemoteDisconnected("closed without response"),
                )
            ),
            "ECONNRESET",
        ),
        (
            requests.exceptions.ConnectionError(
                ProtocolError("Connection aborted.", http.client.BadStatusLine("SSH"))
            ),
            "EPROTO",
        ),
        (
            requests.exceptions.SSLError(
                _max_retries(Urllib3SSLError(_cert_verify_error(20)))
            ),
            "X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY",
        ),
        (
            requests.exceptions.SSLError(
                _max_retries(Urllib3SSLError(_cert_verify_error(10)))
            ),
            "X509_V_ERR_CERT_HAS_EXPIRED",
        ),
        (
            requests.exceptions.SSLError(
                _max_retries(Urllib3SSLError(_cert_verify_error(62)))
            ),
            "X509_V_ERR_HOSTNAME_MISMATCH",
        ),
        (
            requests.exceptions.SSLError(
                _max_retries(Urllib3SSLError(_cert_verify_error(24)))
            ),
            "X509_V_ERR_NO_ISSUER_PUBLIC_KEY",
        ),
        (
            requests.exceptions.SSLError(
                _max_retries(Urllib3SSLError(_cert_verify_error(79)))
            ),
            "X509_V_ERR_INVALID_CA",
        ),
        (
            requests.exceptions.SSLError(
                _max_retries(Urllib3SSLError(_cert_verify_error(-1)))
            ),
            "EPROTO",
        ),
        (
            requests.exceptions.SSLError(
                _max_retries(
                    Urllib3SSLError(ssl.SSLError(1, "[SSL] wrong version number"))
                )
            ),
            "EPROTO",
        ),
        (
            requests.exceptions.ProxyError(
                _max_retries(
                    Urllib3ProxyError(
                        "Unable to connect to proxy",
                        _caused_by(
                            NewConnectionError(_CONN, "Failed to establish"),
                            ConnectionRefusedError(errno.ECONNREFUSED, "refused"),
                        ),
                    )
                )
            ),
            "ECONNREFUSED",
        ),
        (
            requests.exceptions.ProxyError(
                _max_retries(
                    Urllib3ProxyError(
                        "Unable to connect to proxy",
                        _caused_by(
                            ConnectTimeoutError(_CONN, "Connection timed out"),
                            TimeoutError("timed out"),
                        ),
                    )
                )
            ),
            "ETIMEDOUT",
        ),
        (requests.exceptions.ConnectTimeout("timed out"), "ETIMEDOUT"),
        (requests.exceptions.ReadTimeout("timed out"), "ETIMEDOUT"),
        (requests.exceptions.RequestException("unexpected"), None),
    ],
)
def test_get_request_error_code__request_failed__returns_expected_code(
    error: requests.RequestException,
    expected_code: str | None,
) -> None:
    # Given / When
    code = get_request_error_code(error)

    # Then
    assert code == expected_code
