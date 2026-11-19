import errno
import http.client
import socket
import ssl

import pytest
import requests
from urllib3.exceptions import (
    MaxRetryError,
    NameResolutionError,
    NewConnectionError,
    ProtocolError,
)
from urllib3.exceptions import ProxyError as Urllib3ProxyError
from urllib3.exceptions import SSLError as Urllib3SSLError

from core.network import get_request_error_code


def _caused_by(error: BaseException, cause: BaseException) -> BaseException:
    error.__cause__ = cause
    return error


def _max_retries(reason: Exception) -> MaxRetryError:
    # How requests' HTTPAdapter receives connection failures from urllib3.
    return MaxRetryError(None, "/", reason=reason)  # type: ignore[arg-type]


def _cert_verify_error(verify_code: int) -> ssl.SSLCertVerificationError:
    error = ssl.SSLCertVerificationError(1, "certificate verify failed")
    error.verify_code = verify_code
    return error


def _new_connection_error(cause: OSError) -> NewConnectionError:
    return _caused_by(  # type: ignore[return-value]
        NewConnectionError(None, "Failed to establish a new connection"),  # type: ignore[arg-type]
        cause,
    )


@pytest.mark.parametrize(
    "error, expected_code",
    [
        (
            requests.exceptions.ConnectionError(
                _max_retries(
                    _new_connection_error(
                        ConnectionRefusedError(errno.ECONNREFUSED, "refused")
                    )
                )
            ),
            "ECONNREFUSED",
        ),
        (
            requests.exceptions.ConnectionError(
                _max_retries(
                    _new_connection_error(OSError(errno.EHOSTUNREACH, "no route"))
                )
            ),
            "EHOSTUNREACH",
        ),
        (
            requests.exceptions.ConnectionError(
                _max_retries(
                    _caused_by(
                        NameResolutionError("example.com", None, None),  # type: ignore[arg-type]
                        socket.gaierror(socket.EAI_NONAME, "Name not known"),
                    )
                )
            ),
            "ENOTFOUND",
        ),
        (
            requests.exceptions.ConnectionError(
                _max_retries(
                    _caused_by(
                        NameResolutionError("example.com", None, None),  # type: ignore[arg-type]
                        socket.gaierror(socket.EAI_AGAIN, "Temporary failure"),
                    )
                )
            ),
            "EAI_AGAIN",
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
            "UNABLE_TO_GET_ISSUER_CERT_LOCALLY",
        ),
        (
            requests.exceptions.SSLError(
                _max_retries(Urllib3SSLError(_cert_verify_error(10)))
            ),
            "CERT_HAS_EXPIRED",
        ),
        (
            requests.exceptions.SSLError(
                _max_retries(Urllib3SSLError(_cert_verify_error(62)))
            ),
            "ERR_TLS_CERT_ALTNAME_INVALID",
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
                        _new_connection_error(
                            ConnectionRefusedError(errno.ECONNREFUSED, "refused")
                        ),
                    )
                )
            ),
            "ECONNREFUSED",
        ),
        (requests.exceptions.ConnectTimeout("timed out"), "ETIMEDOUT"),
        (requests.exceptions.ReadTimeout("timed out"), "ESOCKETTIMEDOUT"),
        (requests.exceptions.RequestException("unexpected"), "UNKNOWN"),
    ],
)
def test_get_request_error_code__request_failed__returns_expected_code(
    error: requests.RequestException,
    expected_code: str,
) -> None:
    # Given / When
    code = get_request_error_code(error)

    # Then
    assert code == expected_code
