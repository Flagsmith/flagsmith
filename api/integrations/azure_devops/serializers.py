from typing import Any

from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.common.serializers import BaseProjectIntegrationModelSerializer

WRITE_ONLY_PLACEHOLDER = "write-only"


class AzureDevOpsConfigurationSerializer(BaseProjectIntegrationModelSerializer):
    class Meta:
        model = AzureDevOpsConfiguration
        fields = (
            "id",
            "organisation_url",
            "personal_access_token",
            "labeling_enabled",
            "tagging_enabled",
        )

    def to_representation(self, instance: AzureDevOpsConfiguration) -> dict[str, Any]:
        data = super().to_representation(instance)
        data["personal_access_token"] = WRITE_ONLY_PLACEHOLDER
        return data
