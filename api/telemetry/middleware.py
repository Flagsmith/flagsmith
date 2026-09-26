import re
from collections.abc import Callable
from typing import cast

import structlog
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from opentelemetry import baggage

from telemetry.spans import get_span_attribute

CLI_USER_AGENT_PATTERN = re.compile(
    r"^flagsmith-cli/(?P<version>.+) \((?P<os>[^/()]+)/(?P<arch>[^/()]+)\)$"
)


def _get_organisation_id_from_request_context(
    request: HttpRequest,
) -> int | None:
    # Set by the permission layer for organisations the user belongs to
    if isinstance(
        organisation_id := get_span_attribute("organisation.id"),
        int,
    ):
        return organisation_id

    if getattr(request.user, "is_master_api_key_user", False):
        from api_keys.user import APIKeyUser

        assert isinstance(request.user, APIKeyUser)
        return cast(int, request.user.key.organisation_id)

    return None


class MCPUsageLoggerMiddleware:
    """Emit telemetry events for MCP usage"""

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if baggage.get_baggage("flagsmith.client.name") != "flagsmith-mcp":
            return response

        if not request.user or not request.user.is_authenticated:
            return response

        logger = structlog.get_logger("mcp")
        event = {
            # NOTE: The following W3C Baggage items are added by downstream processor
            # - gen_ai.tool.name
            # - flagsmith.mcp.client.name
            # - flagsmith.mcp.client.version
            "status": "error" if response.status_code >= 400 else "success",
        }
        if (org_id := self._get_organisation_id(request)) is not None:
            logger.info("tool.called", organisation__id=org_id, **event)
        else:
            logger.warning("tool.called", organisation__id=None, **event)

        return response

    def _get_organisation_id(self, request: HttpRequest) -> int | None:
        """Obtain the organisation ID from the request context."""
        from organisations.models import Organisation

        if (
            organisation_id := _get_organisation_id_from_request_context(request)
        ) is not None:
            return organisation_id

        assert request.user.is_authenticated  # NOTE: protected upstream
        try:  # Most of the time, the user belongs to one organisation
            return request.user.organisations.get().id
        except (
            Organisation.DoesNotExist,
            Organisation.MultipleObjectsReturned,  # Don't guess
        ):
            return None


class CLIUsageLoggerMiddleware:
    """Emit telemetry events for Flagsmith CLI usage."""

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        match = CLI_USER_AGENT_PATTERN.fullmatch(request.headers.get("User-Agent", ""))
        if match is None:
            return response

        if not request.user or not request.user.is_authenticated:
            return response

        event = {
            "cli__version": match.group("version"),
            "cli__os": match.group("os"),
            "cli__arch": match.group("arch"),
            "status": "error" if response.status_code >= 400 else "success",
        }

        if (
            organisation_id := _get_organisation_id_from_request_context(request)
        ) is not None:
            event["organisation__id"] = organisation_id

        if not getattr(request.user, "is_master_api_key_user", False):
            from users.models import FFAdminUser

            assert isinstance(request.user, FFAdminUser)
            event["amplitude__user_id"] = str(request.user.uuid)

        structlog.get_logger("cli").info("request.made", **event)

        return response
