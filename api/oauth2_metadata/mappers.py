from collections.abc import Iterable
from typing import Any

from oauth2_provider.scopes import get_scopes_backend

from oauth2_metadata.constants import SCOPE_GRANTS
from oauth2_metadata.types import ScopeDescription

_RFC7591_ERROR_CODES: dict[str, str] = {
    "redirect_uris": "invalid_redirect_uri",
    "client_name": "invalid_client_metadata",
    "grant_types": "invalid_client_metadata",
    "response_types": "invalid_client_metadata",
    "token_endpoint_auth_method": "invalid_client_metadata",
}


def map_scopes_to_descriptions(
    scopes: Iterable[str],
) -> dict[str, ScopeDescription]:
    """Describe scopes for a consent screen.

    The label is the scope registry's own one-liner; the grants spell it out.
    A scope with nothing written about it is described by its label alone,
    so an added scope is never presented as granting nothing.
    """
    all_scopes: dict[str, str] = get_scopes_backend().get_all_scopes()
    return {
        scope: ScopeDescription(
            label=all_scopes.get(scope, scope),
            grants=list(SCOPE_GRANTS.get(scope, ())),
        )
        for scope in scopes
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
