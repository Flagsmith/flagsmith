import json
import re
from functools import wraps
from typing import Any, Callable

import requests
from django.conf import settings
from django.db.utils import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from integrations.github.client import (
    ResourceType,
    delete_github_installation,
    fetch_github_repositories,
    fetch_github_resource,
)
from integrations.github.exceptions import DuplicateGitHubIntegration
from integrations.github.helpers import github_webhook_payload_is_valid
from integrations.github.models import GithubConfiguration, GithubRepository
from integrations.github.permissions import HasPermissionToGithubConfiguration
from integrations.github.serializers import (
    GithubConfigurationSerializer,
    GithubRepositorySerializer,
    RepoQuerySerializer,
)
from organisations.permissions.permissions import GithubIsAdminOrganisation


def github_auth_required(func):
    @wraps(func)
    def wrapper(request, organisation_pk):

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
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Response:
            try:
                return func(*args, **kwargs)
            except requests.RequestException as e:
                return Response(
                    data={
                        "detail": (
                            f"{error or 'Failed to retrieve requested information from GitHub API.'}"
                            f" Error: {str(e)}"
                        )
                    },
                    content_type="application/json",
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return wrapper

    return decorator


class GithubConfigurationViewSet(viewsets.ModelViewSet):
    permission_classes = (
        IsAuthenticated,
        HasPermissionToGithubConfiguration,
        GithubIsAdminOrganisation,
    )
    serializer_class = GithubConfigurationSerializer
    model_class = GithubConfiguration

    def perform_create(self, serializer):
        organisation_id = self.kwargs["organisation_pk"]
        serializer.save(organisation_id=organisation_id)

    def get_queryset(self):
        return GithubConfiguration.objects.filter(
            organisation_id=self.kwargs["organisation_pk"]
        )

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            if re.search(r"Key \(organisation_id\)=\(\d+\) already exists", str(e)):
                raise DuplicateGitHubIntegration

    def destroy(self, request, *args, **kwargs):
        github_response = delete_github_installation(self.get_object().installation_id)
        if github_response.status_code != 204:
            return Response(
                data={
                    "detail": (
                        "Failed to delete GitHub Installation."
                        f" Github API returned status code: {github_response.status_code}."
                        f" Error returned: {github_response.json()['message']}"
                    )
                },
                content_type="application/json",
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return super().destroy(request, *args, **kwargs)


class GithubRepositoryViewSet(viewsets.ModelViewSet):
    permission_classes = (
        IsAuthenticated,
        HasPermissionToGithubConfiguration,
        GithubIsAdminOrganisation,
    )
    serializer_class = GithubRepositorySerializer
    model_class = GithubRepository

    def perform_create(self, serializer):
        github_configuration_id = self.kwargs["github_pk"]
        serializer.save(github_configuration_id=github_configuration_id)

    def get_queryset(self):
        github_pk = self.kwargs.get("github_pk")
        if github_pk is not None:
            try:
                int(github_pk)
            except ValueError:
                raise ValidationError({"github_pk": ["Must be an integer"]})
            return GithubRepository.objects.filter(github_configuration=github_pk)

    def create(self, request, *args, **kwargs):

        try:
            return super().create(request, *args, **kwargs)

        except IntegrityError as e:
            if re.search(
                r"Key \(github_configuration_id, project_id, repository_owner, repository_name\)",
                str(e),
            ) and re.search(r"already exists.$", str(e)):
                raise ValidationError(
                    detail="Duplication error. The GitHub repository already linked"
                )


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
@github_auth_required
@github_api_call_error_handler(error="Failed to retrieve GitHub pull requests.")
def fetch_pull_requests(request, organisation_pk) -> Response:
    query_serializer = RepoQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    repo_owner = str(query_serializer.validated_data.get("repo_owner"))
    repo_name = str(query_serializer.validated_data.get("repo_name"))

    return Response(
        fetch_github_resource(
            ResourceType.PULL_REQUESTS, organisation_pk, repo_owner, repo_name
        ).json()
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
@github_auth_required
@github_api_call_error_handler(error="Failed to retrieve GitHub pull requests.")
def fetch_issues(request, organisation_pk) -> Response:
    query_serializer = RepoQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    repo_owner = str(query_serializer.validated_data.get("repo_owner"))
    repo_name = str(query_serializer.validated_data.get("repo_name"))

    response = fetch_github_resource(
        ResourceType.ISSUES, organisation_pk, repo_owner, repo_name
    ).json()
    if response is not None:
        if isinstance(response, list):
            filtered_data = [issue for issue in response if "pull_request" not in issue]
            return Response(filtered_data)
    return Response(
        data={"detail": "Invalid response"},
        content_type="application/json",
        status=status.HTTP_502_BAD_GATEWAY,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, GithubIsAdminOrganisation])
@github_api_call_error_handler(error="Failed to retrieve GitHub pull requests.")
def fetch_repositories(request, organisation_pk: int) -> Response:
    installation_id = request.GET.get("installation_id")

    if not installation_id:
        return Response(
            data={"detail": "Missing installation_id parameter"},
            content_type="application/json",
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(fetch_github_repositories(installation_id).json())


@api_view(["POST"])
@permission_classes([AllowAny])
def github_webhook(request) -> Response:
    secret = settings.GITHUB_WEBHOOK_SECRET
    signature = request.headers.get("X-Hub-Signature")
    github_event = request.headers.get("x-github-event")
    payload = request.body
    if github_webhook_payload_is_valid(
        payload_body=payload, secret_token=secret, signature_header=signature
    ):
        data = json.loads(payload.decode("utf-8"))
        # handle GitHub Webhook "installation" event with action type "deleted"
        if github_event == "installation" and data["action"] == "deleted":
            GithubConfiguration.objects.filter(
                installation_id=data["installation"]["id"]
            ).delete()
            return Response({"detail": "Event processed"}, status=200)
        else:
            return Response({"detail": "Event bypassed"}, status=200)
    else:
        return Response({"error": "Invalid signature"}, status=400)
