import logging
from functools import wraps
from typing import Any, Callable

import requests
from django.db.utils import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from integrations.gitlab.client import (
    create_flagsmith_flag_label,
    fetch_gitlab_project_members,
    fetch_gitlab_projects,
    fetch_search_gitlab_resource,
)
from integrations.gitlab.dataclasses import (
    IssueQueryParams,
    PaginatedQueryParams,
    ProjectQueryParams,
)
from integrations.gitlab.exceptions import DuplicateGitLabIntegration
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.permissions import HasPermissionToGitLabConfiguration
from integrations.gitlab.serializers import (
    GitLabConfigurationCreateSerializer,
    GitLabConfigurationSerializer,
    IssueQueryParamsSerializer,
    PaginatedQueryParamsSerializer,
    ProjectQueryParamsSerializer,
)

logger = logging.getLogger(__name__)


def gitlab_auth_required(
    func: Callable[..., Response],
) -> Callable[..., Response]:
    @wraps(func)
    def wrapper(request: Request, project_pk: int, **kwargs: Any) -> Response:
        if not GitLabConfiguration.has_gitlab_configuration(project_id=project_pk):
            return Response(
                data={
                    "detail": "This project doesn't have a valid GitLab configuration"
                },
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST,
            )
        return func(request, project_pk, **kwargs)

    return wrapper


def gitlab_api_call_error_handler(
    error: str | None = None,
) -> Callable[..., Callable[..., Response]]:
    def decorator(
        func: Callable[..., Response],
    ) -> Callable[..., Response]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Response:
            default_error = "Failed to retrieve requested information from GitLab API."
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                detail = f"{error or default_error} Error: {e}"
                logger.error(detail, exc_info=e)
                return Response(
                    data={"detail": detail},
                    content_type="application/json",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except requests.RequestException as e:
                detail = f"{error or default_error} Error: {e}"
                logger.error(detail, exc_info=e)
                return Response(
                    data={"detail": detail},
                    content_type="application/json",
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return wrapper

    return decorator


class GitLabConfigurationViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    permission_classes = (
        IsAuthenticated,
        HasPermissionToGitLabConfiguration,
    )
    model_class = GitLabConfiguration

    def get_serializer_class(
        self,
    ) -> type[GitLabConfigurationSerializer] | type[GitLabConfigurationCreateSerializer]:
        if self.action == "create":
            return GitLabConfigurationCreateSerializer
        return GitLabConfigurationSerializer

    def perform_create(  # type: ignore[override]
        self,
        serializer: GitLabConfigurationCreateSerializer,
    ) -> None:
        project_id = self.kwargs["project_pk"]
        serializer.save(project_id=project_id)
        if serializer.validated_data.get(
            "tagging_enabled", False
        ) and serializer.validated_data.get("gitlab_project_id"):
            create_flagsmith_flag_label(
                instance_url=serializer.validated_data["gitlab_instance_url"],
                access_token=serializer.validated_data["access_token"],
                gitlab_project_id=serializer.validated_data["gitlab_project_id"],
            )

    def get_queryset(self) -> Any:
        if getattr(self, "swagger_fake_view", False):
            return GitLabConfiguration.objects.none()
        return GitLabConfiguration.objects.filter(project_id=self.kwargs["project_pk"])

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            if "already exists" in str(e):
                raise DuplicateGitLabIntegration from e
            raise

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        response: Response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        if request.data.get("tagging_enabled", False) and instance.gitlab_project_id:
            create_flagsmith_flag_label(
                instance_url=instance.gitlab_instance_url,
                access_token=instance.access_token,
                gitlab_project_id=instance.gitlab_project_id,
            )
        return response


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGitLabConfiguration])
@gitlab_auth_required
@gitlab_api_call_error_handler(error="Failed to retrieve GitLab merge requests.")
def fetch_merge_requests(request: Request, project_pk: int) -> Response:
    query_serializer = IssueQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    gitlab_config = GitLabConfiguration.objects.get(
        project_id=project_pk, deleted_at__isnull=True
    )
    data = fetch_search_gitlab_resource(
        resource_type="merge_requests",
        instance_url=gitlab_config.gitlab_instance_url,
        access_token=gitlab_config.access_token,
        params=IssueQueryParams(**query_serializer.validated_data),
    )
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGitLabConfiguration])
@gitlab_auth_required
@gitlab_api_call_error_handler(error="Failed to retrieve GitLab issues.")
def fetch_issues(request: Request, project_pk: int) -> Response:
    query_serializer = IssueQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    gitlab_config = GitLabConfiguration.objects.get(
        project_id=project_pk, deleted_at__isnull=True
    )
    data = fetch_search_gitlab_resource(
        resource_type="issues",
        instance_url=gitlab_config.gitlab_instance_url,
        access_token=gitlab_config.access_token,
        params=IssueQueryParams(**query_serializer.validated_data),
    )
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGitLabConfiguration])
@gitlab_api_call_error_handler(error="Failed to retrieve GitLab projects.")
def fetch_projects(request: Request, project_pk: int) -> Response:
    query_serializer = PaginatedQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    gitlab_config = GitLabConfiguration.objects.get(
        project_id=project_pk, deleted_at__isnull=True
    )
    data = fetch_gitlab_projects(
        instance_url=gitlab_config.gitlab_instance_url,
        access_token=gitlab_config.access_token,
        params=PaginatedQueryParams(**query_serializer.validated_data),
    )
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGitLabConfiguration])
@gitlab_auth_required
@gitlab_api_call_error_handler(error="Failed to retrieve GitLab project members.")
def fetch_project_members(request: Request, project_pk: int) -> Response:
    query_serializer = ProjectQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    gitlab_config = GitLabConfiguration.objects.get(
        project_id=project_pk, deleted_at__isnull=True
    )
    data = fetch_gitlab_project_members(
        instance_url=gitlab_config.gitlab_instance_url,
        access_token=gitlab_config.access_token,
        params=ProjectQueryParams(**query_serializer.validated_data),
    )
    return Response(data=data, status=status.HTTP_200_OK)
