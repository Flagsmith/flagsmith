from rest_framework import viewsets

from integrations.github.models import GithubConfiguration, GithubRepository
from integrations.github.serializers import (
    GithubConfigurationSerializer,
    GithubRepositorySerializer,
)


class GithubConfigurationViewSet(viewsets.ModelViewSet):
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
    serializer_class = GithubRepositorySerializer
    model_class = GithubRepository

    def perform_create(self, serializer):
        github_configuration_id = self.kwargs["github_pk"]
        serializer.save(github_configuration_id=github_configuration_id)

    def get_queryset(self):
        return GithubRepository.objects.filter(
            github_configuration=self.kwargs["github_pk"]
        )
