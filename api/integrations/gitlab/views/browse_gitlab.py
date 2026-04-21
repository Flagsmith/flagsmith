import abc
from typing import Any, Generic

import requests
import structlog
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from structlog.typing import FilteringBoundLogger

from integrations.gitlab.client import (
    GitLabIssue,
    GitLabMergeRequest,
    GitLabPage,
    GitLabProject,
    fetch_gitlab_projects,
    search_gitlab_issues,
    search_gitlab_merge_requests,
)
from integrations.gitlab.client.types import T
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.serializers import (
    PaginatedQueryParamsSerializer,
    SearchQueryParamsSerializer,
)
from projects.permissions import NestedProjectPermissions

logger = structlog.get_logger("gitlab")


class _GitLabListView(ListAPIView, abc.ABC, Generic[T]):  # type: ignore[type-arg]
    permission_classes = [NestedProjectPermissions]
    serializer_class = PaginatedQueryParamsSerializer
    action = "list"  # NestedProjectPermissions reads from ViewSet.action

    @abc.abstractmethod
    def fetch_page(
        self,
        config: GitLabConfiguration,
        validated_data: dict[str, Any],
    ) -> GitLabPage[T]: ...

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            config = self._get_gitlab_config()
        except GitLabConfiguration.DoesNotExist:
            return Response(
                data={"detail": "This project has no GitLab configuration"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            page_data = self.fetch_page(config, serializer.validated_data)
        except requests.RequestException as exc:
            self._log_for(config).error("api_call.failed", exc_info=exc)
            return Response(
                data={"detail": "GitLab API is unreachable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return self._paginated_response(page_data, request)

    def _log_for(self, config: GitLabConfiguration) -> FilteringBoundLogger:
        return logger.bind(  # type: ignore[no-any-return]
            organisation__id=config.project.organisation_id,
            project__id=config.project_id,
        )

    def _get_gitlab_config(self) -> GitLabConfiguration:
        return GitLabConfiguration.objects.get(  # type: ignore[no-any-return]
            project_id=self.kwargs["project_pk"],
            deleted_at__isnull=True,
        )

    def _paginated_response(
        self,
        page_data: GitLabPage[T],
        request: Request,
    ) -> Response:
        current = page_data["current_page"]
        total = page_data["total_pages"]

        def page_url(page: int) -> str:
            params = request.query_params.copy()
            params["page"] = str(page)
            return request.build_absolute_uri(f"{request.path}?{params.urlencode()}")

        return Response(
            {
                "count": page_data["total_count"],
                "results": page_data["results"],
                "next": page_url(current + 1) if current < total else None,
                "previous": page_url(current - 1) if current > 1 else None,
            }
        )


class BrowseGitLabProjects(_GitLabListView[GitLabProject]):
    def fetch_page(
        self,
        config: GitLabConfiguration,
        validated_data: dict[str, Any],
    ) -> GitLabPage[GitLabProject]:
        page_data = fetch_gitlab_projects(
            instance_url=config.gitlab_instance_url,
            access_token=config.access_token,
            page=validated_data["page"],
            page_size=validated_data["page_size"],
        )

        self._log_for(config).info("projects.fetched")
        return page_data


class BrowseGitLabIssues(_GitLabListView[GitLabIssue]):
    serializer_class = SearchQueryParamsSerializer

    def fetch_page(
        self,
        config: GitLabConfiguration,
        validated_data: dict[str, Any],
    ) -> GitLabPage[GitLabIssue]:
        page_data = search_gitlab_issues(
            instance_url=config.gitlab_instance_url,
            access_token=config.access_token,
            gitlab_project_id=validated_data["gitlab_project_id"],
            page=validated_data["page"],
            page_size=validated_data["page_size"],
            search_text=validated_data.get("search_text"),
            state=validated_data.get("state", "opened"),
        )

        self._log_for(config).info(
            "issues.fetched",
            gitlab__project__id=validated_data["gitlab_project_id"],
        )
        return page_data


class BrowseGitLabMergeRequests(_GitLabListView[GitLabMergeRequest]):
    serializer_class = SearchQueryParamsSerializer

    def fetch_page(
        self,
        config: GitLabConfiguration,
        validated_data: dict[str, Any],
    ) -> GitLabPage[GitLabMergeRequest]:
        page_data = search_gitlab_merge_requests(
            instance_url=config.gitlab_instance_url,
            access_token=config.access_token,
            gitlab_project_id=validated_data["gitlab_project_id"],
            page=validated_data["page"],
            page_size=validated_data["page_size"],
            search_text=validated_data.get("search_text"),
            state=validated_data.get("state", "opened"),
        )

        self._log_for(config).info(
            "merge_requests.fetched",
            gitlab__project__id=validated_data["gitlab_project_id"],
        )
        return page_data
