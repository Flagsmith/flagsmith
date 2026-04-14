from integrations.common.serializers import BaseProjectIntegrationModelSerializer
from integrations.gitlab.models import GitLabConfiguration


class GitLabConfigurationSerializer(BaseProjectIntegrationModelSerializer):
    class Meta:
        model = GitLabConfiguration
        fields = ("id", "gitlab_instance_url", "access_token")
        extra_kwargs = {
            "access_token": {"write_only": True},
        }
