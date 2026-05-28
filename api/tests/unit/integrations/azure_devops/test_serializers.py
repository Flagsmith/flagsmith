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


@pytest.mark.django_db
def test_serializer__update_with_placeholder_pat__preserves_existing_token(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    original_token = azure_devops_configuration.personal_access_token
    serializer = AzureDevOpsConfigurationSerializer(
        instance=azure_devops_configuration,
        data={
            "organisation_url": azure_devops_configuration.organisation_url,
            "personal_access_token": WRITE_ONLY_PLACEHOLDER,
        },
    )

    # When
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # Then
    azure_devops_configuration.refresh_from_db()
    assert azure_devops_configuration.personal_access_token == original_token


@pytest.mark.django_db
def test_serializer__update_with_new_pat__persists_new_token(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    new_token = "ado-rotated-token"
    serializer = AzureDevOpsConfigurationSerializer(
        instance=azure_devops_configuration,
        data={
            "organisation_url": azure_devops_configuration.organisation_url,
            "personal_access_token": new_token,
        },
    )

    # When
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # Then
    azure_devops_configuration.refresh_from_db()
    assert azure_devops_configuration.personal_access_token == new_token
