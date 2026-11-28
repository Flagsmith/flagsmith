import re
from collections.abc import Callable
from typing import Literal

import structlog
from common.core.request_context import get_request_context
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from opentelemetry import baggage

# e.g. `flagsmith-cli/2.0.0 (darwin/arm64)`
CLI_USER_AGENT_PATTERN = re.compile(
    r"^flagsmith-cli/(?P<version>[^\s/]+) \((?P<os>[^\s/()]+)/(?P<arch>[^\s/()]+)\)"
)


class ClientUsageLoggerMiddleware:
    """Emit telemetry events for usage of Flagsmith clients, i.e. MCP and CLI"""

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if baggage.get_baggage("flagsmith.client.name") == "flagsmith-mcp":
            self._log_mcp_usage(request, response)
        elif cli := CLI_USER_AGENT_PATTERN.match(request.headers.get("User-Agent", "")):
            self._log_cli_usage(request, response, cli)

        return response

    def _log_mcp_usage(self, request: HttpRequest, response: HttpResponse) -> None:
        if not request.user or not request.user.is_authenticated:
            return

        # NOTE: The following W3C Baggage items are added by downstream processor
        # - gen_ai.tool.name
        # - flagsmith.mcp.client.name
        # - flagsmith.mcp.client.version
        logger = structlog.get_logger("mcp")
        logger = logger.bind(status=self._get_status(response))
        if (org_id := self._get_organisation_id(request)) is not None:
            logger.info("tool.called", organisation__id=org_id)
        else:
            logger.warning("tool.called", organisation__id=None)

    def _log_cli_usage(
        self,
        request: HttpRequest,
        response: HttpResponse,
        cli: re.Match[str],
    ) -> None:
        if not request.user or not request.user.is_authenticated:
            return

        logger = structlog.get_logger("cli")
        logger = logger.bind(
            cli__version=cli["version"],
            cli__os=cli["os"],
            cli__arch=cli["arch"],
            status=self._get_status(response),
        )
        if not getattr(request.user, "is_master_api_key_user", False):
            logger = logger.bind(amplitude__user_id=str(request.user.uuid))

        if (org_id := self._get_organisation_id(request)) is not None:
            logger.info("request.made", organisation__id=org_id)
        else:
            logger.warning("request.made", organisation__id=None)

    def _get_status(self, response: HttpResponse) -> Literal["success", "error"]:
        return "error" if response.status_code >= 400 else "success"

    def _get_organisation_id(self, request: HttpRequest) -> int | None:
        """Obtain the organisation ID from the request context."""
        from organisations.models import Organisation

        if isinstance(organisation_id := get_request_context("organisation__id"), int):
            return organisation_id

        assert request.user.is_authenticated  # NOTE: protected upstream
        try:  # Most of the time, the user belongs to one organisation
            # NOTE: Master API keys belong to exactly one organisation
            return request.user.organisations.get().id
        except (
            Organisation.DoesNotExist,
            Organisation.MultipleObjectsReturned,  # Don't guess
        ):
            return None
