import json
import re
from functools import wraps

import requests
from django.conf import settings
from django.db.utils import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from integrations.github.client import generate_token
from integrations.github.constants import GITHUB_API_URL, GITHUB_API_VERSION
from integrations.github.exceptions import DuplicateGitHubIntegration
from integrations.github.helpers import github_webhook_payload_is_valid
from integrations.github.models import GithubConfiguration, GithubRepository
from integrations.github.permissions import HasPermissionToGithubConfiguration
from integrations.github.serializers import (
    GithubConfigurationSerializer,
    GithubRepositorySerializer,
    RepoQuerySerializer,
)
from organisations.models import Organisation
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
        return GithubRepository.objects.filter(
            github_configuration=self.kwargs["github_pk"]
        )

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
def fetch_pull_requests(request, organisation_pk) -> Response:
    organisation = Organisation.objects.get(id=organisation_pk)
    github_configuration = GithubConfiguration.objects.get(
        organisation=organisation, deleted_at__isnull=True
    )
    token = generate_token(
        github_configuration.installation_id,
        settings.GITHUB_APP_ID,
    )

    query_serializer = RepoQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    repo_owner = query_serializer.validated_data.get("repo_owner")
    repo_name = query_serializer.validated_data.get("repo_name")

    url = f"{GITHUB_API_URL}repos/{repo_owner}/{repo_name}/pulls"

    headers = {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return Response(data)
    except requests.RequestException as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
@github_auth_required
def fetch_issues(request, organisation_pk) -> Response:
    organisation = Organisation.objects.get(id=organisation_pk)
    github_configuration = GithubConfiguration.objects.get(
        organisation=organisation, deleted_at__isnull=True
    )
    token = generate_token(
        github_configuration.installation_id,
        settings.GITHUB_APP_ID,
    )

    query_serializer = RepoQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response({"error": query_serializer.errors}, status=400)

    repo_owner = query_serializer.validated_data.get("repo_owner")
    repo_name = query_serializer.validated_data.get("repo_name")

    url = f"{GITHUB_API_URL}repos/{repo_owner}/{repo_name}/issues"

    headers = {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        filtered_data = [issue for issue in data if "pull_request" not in issue]
        return Response(filtered_data)
    except requests.RequestException as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated, GithubIsAdminOrganisation])
def fetch_repositories(request, organisation_pk: int) -> Response:
    installation_id = request.GET.get("installation_id")

    token = generate_token(
        installation_id,
        settings.GITHUB_APP_ID,
    )

    url = f"{GITHUB_API_URL}installation/repositories"

    headers = {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return Response(data)
    except requests.RequestException as e:
        return Response({"error": str(e)}, status=500)


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
