from functools import wraps

import requests
from django.conf import settings
from django.db.utils import IntegrityError
from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from integrations.github.client import generate_token
from integrations.github.constants import GITHUB_API_URL, GITHUB_API_VERSION
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
        except IntegrityError:
            raise ValidationError(
                detail="Duplication error. The Github repository already linked"
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
@github_auth_required
def fetch_pull_requests(request, organisation_pk):
    organisation = Organisation.objects.get(id=organisation_pk)

    token = generate_token(
        organisation.github_config.installation_id,
        settings.GITHUB_APP_ID,
    )

    query_serializer = RepoQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return JsonResponse({"error": query_serializer.errors}, status=400)

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
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
@github_auth_required
def fetch_issues(request, organisation_pk):
    organisation = Organisation.objects.get(id=organisation_pk)
    token = generate_token(
        organisation.github_config.installation_id,
        settings.GITHUB_APP_ID,
    )

    query_serializer = RepoQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return JsonResponse({"error": query_serializer.errors}, status=400)

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
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated, GithubIsAdminOrganisation])
def fetch_repositories(request, organisation_pk: int):
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
        return JsonResponse({"error": str(e)}, status=500)
