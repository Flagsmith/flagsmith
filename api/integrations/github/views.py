import requests
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from integrations.github.client import generate_token
from integrations.github.constants import (
    GITHUB_API_URL,
    GITHUB_API_VERSION,
    GITHUB_APP_ID,
)
from integrations.github.models import GithubConfiguration, GithubRepository
from integrations.github.permissions import HasPermissionToGithubConfiguration
from integrations.github.serializers import (
    GithubConfigurationSerializer,
    GithubRepositorySerializer,
)
from organisations.models import Organisation


class GithubConfigurationViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, HasPermissionToGithubConfiguration)
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
    permission_classes = (IsAuthenticated, HasPermissionToGithubConfiguration)
    serializer_class = GithubRepositorySerializer
    model_class = GithubRepository

    def perform_create(self, serializer):
        github_configuration_id = self.kwargs["github_pk"]
        serializer.save(github_configuration_id=github_configuration_id)

    def get_queryset(self):
        return GithubRepository.objects.filter(
            github_configuration=self.kwargs["github_pk"]
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
def fetch_pull_requests(request, organisation_pk):
    organisation = Organisation.objects.get(id=organisation_pk)

    token = generate_token(
        organisation.github_config.installation_id,
        GITHUB_APP_ID,
    )

    url = f"{GITHUB_API_URL}repos/novakzaballa/novak-flagsmith-example/pulls"

    headers = {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return Response(data)
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated, HasPermissionToGithubConfiguration])
def fetch_issues(request, organisation_pk):
    organisation = Organisation.objects.get(id=organisation_pk)
    token = generate_token(
        organisation.github_config.installation_id,
        GITHUB_APP_ID,
    )
    url = f"{GITHUB_API_URL}repos/novakzaballa/novak-flagsmith-example/issues"

    headers = {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        filtered_data = [issue for issue in data if "pull_request" not in issue]
        return Response(filtered_data)
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
def fetch_repositories(request):
    installation_id = request.GET.get("installation_id")

    token = generate_token(
        installation_id,
        GITHUB_APP_ID,
    )

    url = f"{GITHUB_API_URL}installation/repositories"

    headers = {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return Response(data)
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
