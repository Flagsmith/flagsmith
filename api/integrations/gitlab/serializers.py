from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework_dataclasses.serializers import DataclassSerializer

from integrations.gitlab.dataclasses import (
    IssueQueryParams,
    PaginatedQueryParams,
    ProjectQueryParams,
)
from integrations.gitlab.models import GitLabConfiguration


class GitLabConfigurationSerializer(ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = GitLabConfiguration
        fields = (
            "id",
            "gitlab_instance_url",
            "webhook_secret",
            "gitlab_project_id",
            "project_name",
            "tagging_enabled",
            "project",
        )
        read_only_fields = ("project",)
        extra_kwargs = {
            "webhook_secret": {"write_only": False},
        }


class GitLabConfigurationCreateSerializer(ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = GitLabConfiguration
        fields = (
            "id",
            "gitlab_instance_url",
            "access_token",
            "webhook_secret",
            "gitlab_project_id",
            "project_name",
            "tagging_enabled",
            "project",
        )
        read_only_fields = ("project",)


class CreateCleanupIssueSerializer(serializers.Serializer):  # type: ignore[type-arg]
    feature_id = serializers.IntegerField()


class PaginatedQueryParamsSerializer(DataclassSerializer):  # type: ignore[type-arg]
    class Meta:
        dataclass = PaginatedQueryParams


class ProjectQueryParamsSerializer(DataclassSerializer):  # type: ignore[type-arg]
    class Meta:
        dataclass = ProjectQueryParams


class IssueQueryParamsSerializer(DataclassSerializer):  # type: ignore[type-arg]
    class Meta:
        dataclass = IssueQueryParams
