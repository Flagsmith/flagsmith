from typing import Any


def is_e2e_request(request: Any) -> bool:
    """
    True when the request carried a valid E2E test auth token.

    `E2ETestMiddleware` sets the flag, and is only installed when
    `E2E_TEST_AUTH_TOKEN` is configured, so this is always False otherwise.
    """
    return getattr(request, "is_e2e", False) is True
