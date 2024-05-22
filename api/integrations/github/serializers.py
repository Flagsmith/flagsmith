from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework_dataclasses.serializers import DataclassSerializer

from integrations.github.dataclasses import IssueQueryParams, RepoQueryParams
from integrations.github.models import GithubConfiguration, GithubRepository


class GithubConfigurationSerializer(ModelSerializer):
    class Meta:
        model = GithubConfiguration
        fields = ("id", "installation_id", "organisation")
        read_only_fields = ("organisation",)


class GithubRepositorySerializer(ModelSerializer):
    class Meta:
        model = GithubRepository
        optional_fields = ("search_text", "page")
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


class RepoQueryParamsSerializer(DataclassSerializer):
    class Meta:
        dataclass = RepoQueryParams


class IssueQueryParamsSerializer(DataclassSerializer):
    class Meta:
        dataclass = IssueQueryParams

    search_in_body = serializers.BooleanField(required=False, default=True)
