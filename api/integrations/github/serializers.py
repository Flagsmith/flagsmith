from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework_dataclasses.serializers import DataclassSerializer

from integrations.github.dataclasses import (
    IssueQueryParams,
    PaginatedQueryParams,
    RepoQueryParams,
)
from integrations.github.models import GithubConfiguration, GitHubRepository


class GithubConfigurationSerializer(ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = GithubConfiguration
        fields = ("id", "installation_id", "organisation")
        read_only_fields = ("organisation",)


class GithubRepositorySerializer(ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = GitHubRepository
        optional_fields = ("search_text", "page")
        fields = (
            "id",
            "github_configuration",
            "project",
            "repository_owner",
            "repository_name",
            "tagging_enabled",
        )
        read_only_fields = (
            "id",
            "github_configuration",
        )


class PaginatedQueryParamsSerializer(DataclassSerializer):  # type: ignore[type-arg]
    class Meta:
        dataclass = PaginatedQueryParams


class RepoQueryParamsSerializer(DataclassSerializer):  # type: ignore[type-arg]
    class Meta:
        dataclass = RepoQueryParams


class IssueQueryParamsSerializer(DataclassSerializer):  # type: ignore[type-arg]
    class Meta:
        dataclass = IssueQueryParams

    search_in_body = serializers.BooleanField(required=False, default=True)
