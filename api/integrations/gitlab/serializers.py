from typing import Any

from rest_framework import serializers

from integrations.common.serializers import BaseProjectIntegrationModelSerializer
from integrations.gitlab.models import GitLabConfiguration

WRITE_ONLY_PLACEHOLDER = "write-only"


class GitLabConfigurationSerializer(BaseProjectIntegrationModelSerializer):
    class Meta:
        model = GitLabConfiguration
        fields = ("id", "gitlab_instance_url", "access_token")

    def to_representation(self, instance: GitLabConfiguration) -> dict[str, Any]:
        data = super().to_representation(instance)
        data["access_token"] = WRITE_ONLY_PLACEHOLDER
        return data


class PaginatedQueryParamsSerializer(serializers.Serializer[None]):
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=100, min_value=1, max_value=100)


class SearchQueryParamsSerializer(PaginatedQueryParamsSerializer):
    gitlab_project_id = serializers.IntegerField()
    search_text = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(default="opened", required=False)
