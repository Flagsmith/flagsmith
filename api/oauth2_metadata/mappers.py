from typing import Any

_RFC7591_ERROR_CODES: dict[str, str] = {
    "redirect_uris": "invalid_redirect_uri",
    "client_name": "invalid_client_metadata",
    "grant_types": "invalid_client_metadata",
    "response_types": "invalid_client_metadata",
    "token_endpoint_auth_method": "invalid_client_metadata",
}


def map_drf_error_to_rfc7591_error_body(errors: dict[str, Any]) -> dict[str, str]:
    """Format DRF serializer errors per RFC 7591 section 3.2.2."""
    first_field = next(iter(errors))
    error_code = _RFC7591_ERROR_CODES.get(first_field, "invalid_client_metadata")

    return {
        "error": error_code,
        "error_description": _first_error_message(errors[first_field]),
    }


def _first_error_message(detail: Any) -> str:
    """Extract the first human-readable message from DRF error details.

    ListField child errors arrive as a dict keyed by list index, so
    positional indexing is not safe here.
    """
    while True:
        if isinstance(detail, dict):
            detail = next(iter(detail.values()))
        elif isinstance(detail, (list, tuple)):
            detail = detail[0]
        else:
            # ErrorDetail is a str subclass; str() drops the repr wrapping.
            return str(detail)
