import pytest

from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.serializers import (
    WRITE_ONLY_PLACEHOLDER,
    AzureDevOpsConfigurationSerializer,
)


@pytest.mark.django_db
def test_serializer__to_representation__masks_personal_access_token(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    serializer = AzureDevOpsConfigurationSerializer(instance=azure_devops_configuration)

    # When
    data = serializer.data

    # Then
    assert data["personal_access_token"] == WRITE_ONLY_PLACEHOLDER
    assert data["organisation_url"] == azure_devops_configuration.organisation_url
    assert data["labeling_enabled"] is False
    assert data["tagging_enabled"] is False
