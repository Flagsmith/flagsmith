from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from integrations.gitlab.models import GitLabConfiguration


class GitLabConfigurationSerializer(ModelSerializer[GitLabConfiguration]):
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


class GitLabConfigurationCreateSerializer(ModelSerializer[GitLabConfiguration]):
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
        extra_kwargs = {
            "access_token": {"write_only": True},
        }


class PaginatedQueryParamsSerializer(serializers.Serializer[None]):
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=100, min_value=1, max_value=100)


class ProjectQueryParamsSerializer(PaginatedQueryParamsSerializer):
    gitlab_project_id = serializers.IntegerField(default=0)
    project_name = serializers.CharField(default="", required=False)


class IssueQueryParamsSerializer(ProjectQueryParamsSerializer):
    search_text = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(default="opened", required=False)
    author = serializers.CharField(required=False)
    assignee = serializers.CharField(required=False)
