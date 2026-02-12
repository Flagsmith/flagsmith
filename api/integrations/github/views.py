import json
import logging
import re
from functools import wraps
from typing import Any, Callable
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.db.utils import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from features.feature_external_resources.models import (
    FeatureExternalResource,
)
from features.feature_external_resources.models import (
    ResourceType as ExternalResourceType,
)
from features.models import Feature
from integrations.github.client import (
    ResourceType,
    create_flagsmith_flag_label,
    create_github_issue,
    delete_github_installation,
    fetch_github_repo_contributors,
    fetch_github_repositories,
    fetch_search_github_resource,
)
from integrations.github.constants import (
    CLEANUP_ISSUE_BODY,
    CLEANUP_ISSUE_TITLE,
)
from integrations.github.exceptions import DuplicateGitHubIntegration
from integrations.github.github import (
    handle_github_webhook_event,
    tag_by_event_type,
)
from integrations.github.helpers import github_webhook_payload_is_valid
from integrations.github.models import GithubConfiguration, GitHubRepository
from integrations.github.permissions import HasPermissionToGithubConfiguration
from integrations.github.serializers import (
    CreateCleanupIssueSerializer,
    GithubConfigurationSerializer,
    GithubRepositorySerializer,
    IssueQueryParamsSerializer,
    PaginatedQueryParamsSerializer,
    RepoQueryParamsSerializer,
)
from organisations.permissions.permissions import GithubIsAdminOrganisation
from projects.code_references.services import get_code_references_for_feature_flag

logger = logging.getLogger(__name__)


def github_auth_required(func):  # type: ignore[no-untyped-def]
    @wraps(func)
    def wrapper(request, organisation_pk):  # type: ignore[no-untyped-def]
        if not GithubConfiguration.has_github_configuration(
            organisation_id=organisation_pk
        ):
            return Response(
                data={
                    "detail": "This Organisation doesn't have a valid GitHub Configuration"
                },
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST,
            )
        return func(request, organisation_pk)

    return wrapper


def github_api_call_error_handler(
    error: str | None = None,
) -> Callable[..., Callable[..., Any]]:
    def decorator(func):  # type: ignore[no-untyped-def]
        @wraps(func)
        def wrapper(*args, **kwargs) -> Response:  # type: ignore[no-untyped-def]
            default_error = "Failed to retrieve requested information from GitHub API."
            try:
                return func(*args, **kwargs)  # type: ignore[no-any-return]
            except ValueError as e:
                return Response(
                    data={"detail": (f"{error or default_error} Error: {str(e)}")},
                    content_type="application/json",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except requests.RequestException as e:
                logger.error(f"{error or default_error} Error: {str(e)}", exc_info=e)
                return Response(
                    data={"detail": (f"{error or default_error} Error: {str(e)}")},
                    content_type="application/json",
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return wrapper

    return decorator


class GithubConfigurationViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    permission_classes = (
        IsAuthenticated,
        HasPermissionToGithubConfiguration,
        GithubIsAdminOrganisation,
    )
    serializer_class = GithubConfigurationSerializer
    model_class = GithubConfiguration

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        organisation_id = self.kwargs["organisation_pk"]
        serializer.save(organisation_id=organisation_id)

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return GithubConfiguration.objects.none()

        return GithubConfiguration.objects.filter(
            organisation_id=self.kwargs["organisation_pk"]
        )

    def create(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            if re.search(r"Key \(organisation_id\)=\(\d+\) already exists", str(e)):
                raise DuplicateGitHubIntegration

    @github_api_call_error_handler(error="Failed to delete GitHub Installation.")
    def destroy(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        delete_github_installation(self.get_object().installation_id)
        return super().destroy(request, *args, **kwargs)


class GithubRepositoryViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    permission_classes = (
        IsAuthenticated,
        HasPermissionToGithubConfiguration,
        GithubIsAdminOrganisation,
    )
    serializer_class = GithubRepositorySerializer
    model_class = GitHubRepository

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        github_configuration_id = self.kwargs["github_pk"]
        serializer.save(github_configuration_id=github_configuration_id)

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return GitHubRepository.objects.none()

        try:
            if github_pk := self.kwargs.get("github_pk"):
                int(github_pk)
                return GitHubRepository.objects.filter(github_configuration=github_pk)
        except ValueError:
            raise ValidationError({"github_pk": ["Must be an integer"]})

    def create(self, request, *args, **kwargs) -> Response | None:  # type: ignore[no-untyped-def,return,override]
        try:
            response: Response = super().create(request, *args, **kwargs)
            github_configuration: GithubConfiguration = GithubConfiguration.objects.get(
                id=self.kwargs["github_pk"]
            )
            if request.data.get("tagging_enabled", False):
                create_flagsmith_flag_label(
                    installation_id=github_configuration.installation_id,
                    owner=request.data.get("repository_owner"),
                    repo=request.data.get("repository_name"),
                )
            return response

        except IntegrityError as e:
            if re.search(
                r"Key \(github_configuration_id, project_id, repository_owner, repository_name\)",
                str(e),
            ) and re.search(r"already exists.$", str(e)):
                raise ValidationError(
                    detail="Duplication error. The GitHub repository already linked"
                )

    def update(self, request, *args, **kwargs) -> Response | None:  # type: ignore[no-untyped-def,override]
        response: Response = super().update(request, *args, **kwargs)
        github_configuration: GithubConfiguration = GithubConfiguration.objects.get(
            id=self.kwargs["github_pk"]
        )
        if request.data.get("tagging_enabled", False):
            create_flagsmith_flag_label(
                installation_id=github_configuration.installation_id,
                owner=request.data.get("repository_owner"),
                repo=request.data.get("repository_name"),
            )
        return response


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
@github_auth_required  # type: ignore[misc]
@github_api_call_error_handler(error="Failed to retrieve GitHub pull requests.")
def fetch_pull_requests(request, organisation_pk) -> Response:  # type: ignore[no-untyped-def]
    query_serializer = IssueQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    data = fetch_search_github_resource(
        resource_type=ResourceType.PULL_REQUESTS,
        organisation_id=organisation_pk,
        params=query_serializer.validated_data,
    )
    return Response(
        data=data,
        content_type="application/json",
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
@github_auth_required  # type: ignore[misc]
@github_api_call_error_handler(error="Failed to retrieve GitHub issues.")
def fetch_issues(request, organisation_pk) -> Response | None:  # type: ignore[no-untyped-def]
    query_serializer = IssueQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    data = fetch_search_github_resource(
        resource_type=ResourceType.ISSUES,
        organisation_id=organisation_pk,
        params=query_serializer.validated_data,
    )
    return Response(
        data=data,
        content_type="application/json",
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, GithubIsAdminOrganisation])
@github_api_call_error_handler(error="Failed to retrieve GitHub repositories.")
def fetch_repositories(request, organisation_pk: int) -> Response | None:  # type: ignore[no-untyped-def]
    query_serializer = PaginatedQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)
    installation_id = request.GET.get("installation_id")

    if not installation_id:
        return Response(
            data={"detail": "Missing installation_id parameter"},
            content_type="application/json",
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = fetch_github_repositories(
        installation_id=installation_id, params=query_serializer.validated_data
    )
    return Response(
        data=data,
        content_type="application/json",
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
@github_auth_required  # type: ignore[misc]
@github_api_call_error_handler(error="Failed to retrieve GitHub repo contributors.")
def fetch_repo_contributors(request, organisation_pk) -> Response:  # type: ignore[no-untyped-def]
    query_serializer = RepoQueryParamsSerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    response = fetch_github_repo_contributors(
        organisation_id=organisation_pk, params=query_serializer.validated_data
    )

    return Response(
        data=response,
        content_type="application/json",
        status=status.HTTP_200_OK,
    )


def _get_github_api_url(repository_url: str) -> str:
    """Derive the GitHub API base URL from a repository URL.

    For github.com: https://api.github.com/
    For enterprise: https://{host}/api/v3/
    """
    parsed = urlparse(repository_url)
    if parsed.hostname == "github.com":
        return "https://api.github.com/"
    return f"{parsed.scheme}://{parsed.hostname}/api/v3/"


@api_view(["POST"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
@github_api_call_error_handler(error="Failed to create GitHub cleanup issue.")
def create_cleanup_issue(request, organisation_pk: int) -> Response:  # type: ignore[no-untyped-def]
    serializer = CreateCleanupIssueSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    github_pat: str = settings.FEATURE_LIFECYCLE_GITHUB_PAT
    if not github_pat:
        return Response(
            data={"detail": "GitHub PAT is not configured."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    feature_id: int = serializer.validated_data["feature_id"]

    # Validate the feature exists and belongs to this org.
    try:
        feature = Feature.objects.get(
            id=feature_id,
            project__organisation_id=organisation_pk,
        )
    except Feature.DoesNotExist:
        return Response(
            data={"detail": "Feature not found in this organisation."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Get code references for the feature across all repositories.
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
        # Format code references as markdown list.
        references_text = "\n".join(
            f"- [`{ref.file_path}#L{ref.line_number}`]({ref.permalink})"
            for ref in summary.code_references
        )
        issue_body = CLEANUP_ISSUE_BODY % (feature.name, references_text)

        # Parse owner/name from repository_url.
        url_parts = summary.repository_url.rstrip("/").split("/")
        owner = url_parts[-2]
        repo = url_parts[-1]

        api_url = _get_github_api_url(summary.repository_url)
        github_response = create_github_issue(
            github_pat=github_pat,
            api_url=api_url,
            owner=owner,
            repo=repo,
            title=issue_title,
            body=issue_body,
        )

        # Link the issue to the feature.
        issue_url: str = github_response["html_url"]
        metadata = json.dumps(
            {
                "title": github_response["title"],
                "state": github_response["state"],
            }
        )
        try:
            FeatureExternalResource.objects.create(
                url=issue_url,
                type=ExternalResourceType.GITHUB_ISSUE,
                feature=feature,
                metadata=metadata,
            )
        except IntegrityError:
            pass

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([AllowAny])
def github_webhook(request) -> Response:  # type: ignore[no-untyped-def]
    secret = settings.GITHUB_WEBHOOK_SECRET
    signature = request.headers.get("X-Hub-Signature")
    github_event = request.headers.get("x-github-event")
    payload = request.body
    if github_webhook_payload_is_valid(
        payload_body=payload, secret_token=secret, signature_header=signature
    ):
        data = json.loads(payload.decode("utf-8"))
        if github_event == "installation" or github_event in tag_by_event_type:
            handle_github_webhook_event(event_type=github_event, payload=data)
            return Response({"detail": "Event processed"}, status=200)
        else:
            return Response({"detail": "Event bypassed"}, status=200)
    else:
        return Response({"error": "Invalid signature"}, status=400)
