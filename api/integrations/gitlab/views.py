import json
import logging
from functools import wraps
from typing import Any, Callable

import requests
from django.db.utils import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from features.feature_external_resources.models import (
    FeatureExternalResource,
)
from features.feature_external_resources.models import (
    ResourceType as ExternalResourceType,
)
from features.models import Feature
from integrations.gitlab.client import (
    create_flagsmith_flag_label,
    create_gitlab_issue,
    fetch_gitlab_project_members,
    fetch_gitlab_projects,
    fetch_search_gitlab_resource,
)
from integrations.gitlab.constants import (
    CLEANUP_ISSUE_BODY,
    CLEANUP_ISSUE_TITLE,
)
from integrations.gitlab.exceptions import DuplicateGitLabIntegration
from integrations.gitlab.gitlab import (
    handle_gitlab_webhook_event,
)
from integrations.gitlab.helpers import gitlab_webhook_payload_is_valid
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.permissions import HasPermissionToGitlabConfiguration
from integrations.gitlab.serializers import (
    CreateCleanupIssueSerializer,
    GitLabConfigurationCreateSerializer,
    GitLabConfigurationSerializer,
    IssueQueryParamsSerializer,
    PaginatedQueryParamsSerializer,
    ProjectQueryParamsSerializer,
)
from projects.code_references.services import get_code_references_for_feature_flag

logger = logging.getLogger(__name__)


def gitlab_auth_required(func):  # type: ignore[no-untyped-def]
    @wraps(func)
    def wrapper(request, project_pk):  # type: ignore[no-untyped-def]
        if not GitLabConfiguration.has_gitlab_configuration(
            project_id=project_pk
        ):
            return Response(
                data={
                    "detail": "This Project doesn't have a valid GitLab Configuration"
                },
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST,
            )
        return func(request, project_pk)

    return wrapper


def gitlab_api_call_error_handler(
    error: str | None = None,
) -> Callable[..., Callable[..., Any]]:
    def decorator(func):  # type: ignore[no-untyped-def]
        @wraps(func)
        def wrapper(*args, **kwargs) -> Response:  # type: ignore[no-untyped-def]
            default_error = "Failed to retrieve requested information from GitLab API."
            try:
                return func(*args, **kwargs)  # type: ignore[no-any-return]
            except ValueError as e:
                logger.error(f"{error or default_error} Error: {str(e)}", exc_info=e)
                return Response(
                    data={"detail": error or default_error},
                    content_type="application/json",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except requests.RequestException as e:
                logger.error(f"{error or default_error} Error: {str(e)}", exc_info=e)
                return Response(
                    data={"detail": error or default_error},
                    content_type="application/json",
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return wrapper

    return decorator


class GitLabConfigurationViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    permission_classes = (
        IsAuthenticated,
        HasPermissionToGitlabConfiguration,
    )
    model_class = GitLabConfiguration

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if self.action == "create":
            return GitLabConfigurationCreateSerializer
        return GitLabConfigurationSerializer

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        project_id = self.kwargs["project_pk"]
        serializer.save(project_id=project_id)
        if serializer.validated_data.get("tagging_enabled", False) and serializer.validated_data.get("gitlab_project_id"):
            create_flagsmith_flag_label(
                instance_url=serializer.validated_data["gitlab_instance_url"],
                access_token=serializer.validated_data["access_token"],
                gitlab_project_id=serializer.validated_data["gitlab_project_id"],
            )

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return GitLabConfiguration.objects.none()

        return GitLabConfiguration.objects.filter(
            project_id=self.kwargs["project_pk"]
        )

    def create(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            if "already exists" in str(e):
                raise DuplicateGitLabIntegration

    def update(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        response: Response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        if request.data.get("tagging_enabled", False) and instance.gitlab_project_id:
            create_flagsmith_flag_label(
                instance_url=instance.gitlab_instance_url,
                access_token=instance.access_token,
                gitlab_project_id=instance.gitlab_project_id,
            )
        return response

    def destroy(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        return super().destroy(request, *args, **kwargs)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGitlabConfiguration])
@gitlab_auth_required  # type: ignore[misc]
@gitlab_api_call_error_handler(error="Failed to retrieve GitLab merge requests.")
def fetch_merge_requests(request, project_pk) -> Response:  # type: ignore[no-untyped-def]
    query_serializer = IssueQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    gitlab_config = GitLabConfiguration.objects.get(
        project_id=project_pk, deleted_at__isnull=True
    )
    data = fetch_search_gitlab_resource(
        resource_type="merge_request",
        instance_url=gitlab_config.gitlab_instance_url,
        access_token=gitlab_config.access_token,
        params=query_serializer.validated_data,
    )
    return Response(data=data, content_type="application/json", status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGitlabConfiguration])
@gitlab_auth_required  # type: ignore[misc]
@gitlab_api_call_error_handler(error="Failed to retrieve GitLab issues.")
def fetch_issues(request, project_pk) -> Response:  # type: ignore[no-untyped-def]
    query_serializer = IssueQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    gitlab_config = GitLabConfiguration.objects.get(
        project_id=project_pk, deleted_at__isnull=True
    )
    data = fetch_search_gitlab_resource(
        resource_type="issue",
        instance_url=gitlab_config.gitlab_instance_url,
        access_token=gitlab_config.access_token,
        params=query_serializer.validated_data,
    )
    return Response(data=data, content_type="application/json", status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGitlabConfiguration])
@gitlab_api_call_error_handler(error="Failed to retrieve GitLab projects.")
def fetch_projects(request, project_pk: int) -> Response | None:  # type: ignore[no-untyped-def]
    query_serializer = PaginatedQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    gitlab_config = GitLabConfiguration.objects.get(
        project_id=project_pk, deleted_at__isnull=True
    )
    data = fetch_gitlab_projects(
        instance_url=gitlab_config.gitlab_instance_url,
        access_token=gitlab_config.access_token,
        params=query_serializer.validated_data,
    )
    return Response(data=data, content_type="application/json", status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGitlabConfiguration])
@gitlab_auth_required  # type: ignore[misc]
@gitlab_api_call_error_handler(error="Failed to retrieve GitLab project members.")
def fetch_project_members(request, project_pk) -> Response:  # type: ignore[no-untyped-def]
    query_serializer = ProjectQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    gitlab_config = GitLabConfiguration.objects.get(
        project_id=project_pk, deleted_at__isnull=True
    )
    response = fetch_gitlab_project_members(
        instance_url=gitlab_config.gitlab_instance_url,
        access_token=gitlab_config.access_token,
        params=query_serializer.validated_data,
    )
    return Response(data=response, content_type="application/json", status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated, HasPermissionToGitlabConfiguration])
@gitlab_api_call_error_handler(error="Failed to create GitLab cleanup issue.")
def create_cleanup_issue(request, project_pk: int) -> Response:  # type: ignore[no-untyped-def]
    serializer = CreateCleanupIssueSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    gitlab_config = GitLabConfiguration.objects.get(
        project_id=project_pk, deleted_at__isnull=True
    )

    feature_id: int = serializer.validated_data["feature_id"]

    try:
        feature = Feature.objects.get(
            id=feature_id,
            project_id=project_pk,
        )
    except Feature.DoesNotExist:
        return Response(
            data={"detail": "Feature not found in this project."},
            status=status.HTTP_404_NOT_FOUND,
        )

    summaries = [
        summary
        for summary in get_code_references_for_feature_flag(feature)
        if summary.code_references
    ]
    if not summaries:
        return Response(
            data={"detail": "No code references found for this feature."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    issue_title = CLEANUP_ISSUE_TITLE % feature.name

    for summary in summaries:
        references_text = "\n".join(
            f"- [`{ref.file_path}#L{ref.line_number}`]({ref.permalink})"
            for ref in summary.code_references
        )
        issue_body = CLEANUP_ISSUE_BODY % (feature.name, references_text)

        # Try to match repository URL to the GitLab config
        url_parts = summary.repository_url.rstrip("/").split("/")
        repo_path = "/".join(url_parts[-2:])  # e.g. "group/project"

        if not gitlab_config.project_name or not gitlab_config.project_name.endswith(repo_path):
            continue

        if not gitlab_config.gitlab_project_id:
            continue

        gitlab_response = create_gitlab_issue(
            instance_url=gitlab_config.gitlab_instance_url,
            access_token=gitlab_config.access_token,
            gitlab_project_id=gitlab_config.gitlab_project_id,
            title=issue_title,
            body=issue_body,
        )

        issue_url: str = gitlab_response["web_url"]
        metadata = json.dumps(
            {
                "title": gitlab_response["title"],
                "state": gitlab_response["state"],
            }
        )
        try:
            FeatureExternalResource.objects.create(
                url=issue_url,
                type=ExternalResourceType.GITLAB_ISSUE,
                feature=feature,
                metadata=metadata,
            )
        except IntegrityError:
            pass

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([AllowAny])
def gitlab_webhook(request, project_pk: int) -> Response:  # type: ignore[no-untyped-def]
    gitlab_token = request.headers.get("X-Gitlab-Token")
    gitlab_event = request.headers.get("X-Gitlab-Event")

    try:
        gitlab_config = GitLabConfiguration.objects.get(
            project_id=project_pk, deleted_at__isnull=True
        )
    except GitLabConfiguration.DoesNotExist:
        return Response(
            {"error": "No GitLab configuration found for this project"},
            status=404,
        )

    if not gitlab_webhook_payload_is_valid(
        secret_token=gitlab_config.webhook_secret,
        gitlab_token_header=gitlab_token,
    ):
        return Response({"error": "Invalid token"}, status=400)

    data = json.loads(request.body.decode("utf-8"))

    # Map GitLab event header to our event types
    event_type_map = {
        "Merge Request Hook": "merge_request",
        "Issue Hook": "issue",
    }

    event_type = event_type_map.get(gitlab_event or "")
    if event_type:
        handle_gitlab_webhook_event(event_type=event_type, payload=data)
        return Response({"detail": "Event processed"}, status=200)
    else:
        return Response({"detail": "Event bypassed"}, status=200)
