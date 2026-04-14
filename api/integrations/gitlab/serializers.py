from typing import Any

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
