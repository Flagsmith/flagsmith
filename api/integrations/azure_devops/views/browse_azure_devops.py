import abc
from typing import Any, Sequence, cast

import requests
import structlog
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from structlog.typing import FilteringBoundLogger

from integrations.azure_devops.client import (
    list_projects,
    list_pull_requests,
    list_repositories,
    list_work_items,
)
from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsNotFoundError,
)
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.serializers.browse import (
    AdoBrowseQueryParamsSerializer,
    AdoPullRequestsQueryParamsSerializer,
    AdoRepositoriesQueryParamsSerializer,
    AdoWorkItemsQueryParamsSerializer,
)
from projects.permissions import NestedProjectPermissions

logger = structlog.get_logger("azure_devops")


class _AdoListView(ListAPIView, abc.ABC):  # type: ignore[type-arg]
    permission_classes = [NestedProjectPermissions]
    serializer_class: type[Serializer[Any]] = AdoBrowseQueryParamsSerializer
    action = "list"  # NestedProjectPermissions reads from ViewSet.action

    @abc.abstractmethod
    def fetch(
        self,
        config: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> tuple[Sequence[dict[str, Any]], str | None]:
        """Return (results, next_continuation_token)."""

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            config = self._get_config()
        except AzureDevOpsConfiguration.DoesNotExist:
            return Response(
                data={"detail": "This project has no Azure DevOps configuration"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            results, next_token = self.fetch(config, serializer.validated_data)
        except AzureDevOpsAuthError:
            return Response(
                data={"detail": "Azure DevOps rejected the credentials"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except AzureDevOpsNotFoundError:
            return Response(
                data={"detail": "Azure DevOps could not find the requested resource"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except requests.RequestException as exc:
            self._log_for(config).error("api_call.failed", exc_info=exc)
            return Response(
                data={"detail": "Azure DevOps API is unreachable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return self._paginated_response(results, next_token, request)

    def _log_for(self, config: AzureDevOpsConfiguration) -> FilteringBoundLogger:
        return logger.bind(  # type: ignore[no-any-return]
            organisation__id=config.project.organisation_id,
            project__id=config.project.id,
        )

    def _get_config(self) -> AzureDevOpsConfiguration:
        return AzureDevOpsConfiguration.objects.get(  # type: ignore[no-any-return]
            project_id=self.kwargs["project_pk"],
            deleted_at__isnull=True,
        )

    def _paginated_response(
        self,
        results: Sequence[dict[str, Any]],
        next_token: str | None,
        request: Request,
    ) -> Response:
        next_url: str | None = None
        if next_token:
            params = request.query_params.copy()
            params["continuation_token"] = next_token
            next_url = request.build_absolute_uri(
                f"{request.path}?{params.urlencode()}"
            )
        return Response(
            {
                "results": results,
                "next": next_url,
                "previous": None,
            }
        )


class BrowseAdoProjects(_AdoListView):
    serializer_class = AdoBrowseQueryParamsSerializer

    def fetch(
        self,
        config: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> tuple[Sequence[dict[str, Any]], str | None]:
        page = list_projects(
            organisation_url=config.organisation_url,
            pat=config.personal_access_token,
            top=validated_data["top"],
            continuation_token=validated_data.get("continuation_token"),
        )
        self._log_for(config).info("projects.fetched")
        return (
            cast(Sequence[dict[str, Any]], list(page["results"])),
            page["continuation_token"],
        )


class BrowseAdoRepositories(_AdoListView):
    serializer_class = AdoRepositoriesQueryParamsSerializer

    def fetch(
        self,
        config: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> tuple[Sequence[dict[str, Any]], str | None]:
        repos = list_repositories(
            organisation_url=config.organisation_url,
            pat=config.personal_access_token,
            ado_project_id=validated_data["ado_project_id"],
        )
        self._log_for(config).info(
            "repositories.fetched",
            ado__project__id=validated_data["ado_project_id"],
        )
        # Repositories endpoint isn't paginated by ADO; expose all in one go.
        return cast(Sequence[dict[str, Any]], list(repos)), None


class BrowseAdoPullRequests(_AdoListView):
    serializer_class = AdoPullRequestsQueryParamsSerializer

    def fetch(
        self,
        config: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> tuple[Sequence[dict[str, Any]], str | None]:
        page = list_pull_requests(
            organisation_url=config.organisation_url,
            pat=config.personal_access_token,
            ado_project_id=validated_data["ado_project_id"],
            state=validated_data["state"],
            top=validated_data["top"],
            continuation_token=validated_data.get("continuation_token"),
        )
        self._log_for(config).info(
            "pull_requests.fetched",
            ado__project__id=validated_data["ado_project_id"],
        )
        return (
            cast(Sequence[dict[str, Any]], list(page["results"])),
            page["continuation_token"],
        )


class BrowseAdoWorkItems(_AdoListView):
    serializer_class = AdoWorkItemsQueryParamsSerializer

    def fetch(
        self,
        config: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> tuple[Sequence[dict[str, Any]], str | None]:
        token_int = validated_data.get("continuation_token")
        page = list_work_items(
            organisation_url=config.organisation_url,
            pat=config.personal_access_token,
            ado_project_id=validated_data["ado_project_id"],
            search_text=validated_data.get("search_text") or None,
            state=validated_data.get("state") or None,
            work_item_type=validated_data.get("work_item_type") or None,
            top=validated_data["top"],
            continuation_token=str(token_int) if token_int is not None else None,
        )
        self._log_for(config).info(
            "work_items.fetched",
            ado__project__id=validated_data["ado_project_id"],
        )
        return (
            cast(Sequence[dict[str, Any]], list(page["results"])),
            page["continuation_token"],
        )
