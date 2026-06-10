from collections.abc import Callable

import structlog
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from opentelemetry import baggage


class UndefinedOrganisationError(Exception):
    """The organisation can't be probed from context."""


class MCPUsageLoggerMiddleware:
    """Emit telemetry events for MCP usage"""

    _url_param_to_organisation_lookup = {
        "organisation_pk": "pk",
        "project_pk": "projects__pk",
        "environment_pk": "projects__environments__pk",
        "environment_api_key": "projects__environments__api_key",
    }

    _pk_url_name_to_organisation_lookup = {
        "organisation-projects": "pk",
        "project-detail": "projects__pk",
        "project-environments": "projects__pk",
        "featurestates-detail": "projects__features__feature_states__pk",
        "feature-segment-detail": "projects__features__feature_segments__pk",
    }

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if not request.user or not request.user.is_authenticated:
            return response

        if baggage.get_baggage("flagsmith.client.name") != "flagsmith-mcp":
            return response

        logger = structlog.get_logger("mcp")
        event = {
            # NOTE: The following W3C Baggage items are added by downstream processor
            # - gen_ai.tool.name
            # - flagsmith.mcp.client.name
            # - flagsmith.mcp.client.version
            "status": "error" if response.status_code >= 400 else "success",
        }
        try:
            org_id = self._get_organisation_id(request)
            logger.info("tool.called", organisation__id=org_id, **event)
        except UndefinedOrganisationError:
            logger.warning("tool.called", organisation__id=None, **event)

        return response

    def _get_organisation_id(self, request: HttpRequest) -> int:
        """Obtain the organisation ID from the request context."""
        from organisations.models import Organisation

        assert request.user.is_authenticated  # NOTE: protected upstream
        user_orgs = request.user.organisations.all()
        try:  # Most of the time, the user belongs to one organisation
            return user_orgs.get().id
        except Organisation.MultipleObjectsReturned:
            pass
        except Organisation.DoesNotExist as error:
            raise UndefinedOrganisationError from error

        # Known URL parameter names
        assert request.resolver_match
        kwargs = request.resolver_match.kwargs
        for url_param, value in kwargs.items():
            if lookup := self._url_param_to_organisation_lookup.get(url_param):
                try:
                    return user_orgs.filter(**{lookup: value}).get().id
                except Organisation.DoesNotExist as error:
                    raise UndefinedOrganisationError from error

        # Known URLs using `pk`
        assert (url_name := request.resolver_match.url_name)
        if (lookup := self._pk_url_name_to_organisation_lookup.get(url_name)) and (
            pk := kwargs["pk"]
        ):
            try:
                return user_orgs.filter(**{lookup: pk}).get().id
            except Organisation.DoesNotExist as error:
                raise UndefinedOrganisationError from error

        raise UndefinedOrganisationError
