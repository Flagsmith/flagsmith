from rest_framework.serializers import ModelSerializer

from .models import GithubConfiguration, GithubRepository


class GithubConfigurationSerializer(ModelSerializer):
    class Meta:
        model = GithubConfiguration
        fields = ("id", "installation_id", "organisation")
        read_only_fields = ("organisation",)


class GithubRepositorySerializer(ModelSerializer):
    class Meta:
        model = GithubRepository
        fields = (
            "id",
            "github_configuration",
            "project",
            "repository_owner",
            "repository_name",
        )
        read_only_fields = (
            "id",
            "github_configuration",
        )
