import pytest
from django.db.utils import IntegrityError

from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.models import Project


@pytest.mark.django_db
def test_azure_devops_configuration__defaults__has_expected_defaults(
    project: Project,
) -> None:
    # Given
    config = AzureDevOpsConfiguration.objects.create(
        project=project,
        organisation_url="https://dev.azure.com/test-org",
        personal_access_token="ado-test-token",
    )

    # When
    config.refresh_from_db()

    # Then
    assert config.labeling_enabled is False
    assert config.tagging_enabled is False
    assert config.organisation_url == "https://dev.azure.com/test-org"
    assert config.personal_access_token == "ado-test-token"


@pytest.mark.django_db
def test_azure_devops_configuration__second_for_same_project__raises_integrity_error(
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    duplicate_kwargs = {
        "project": project,
        "organisation_url": "https://dev.azure.com/other",
        "personal_access_token": "ado-other",
    }

    # When / Then — split below per GWT lint rule

    # When
    def create_duplicate() -> None:
        AzureDevOpsConfiguration.objects.create(**duplicate_kwargs)

    # Then
    with pytest.raises(IntegrityError):
        create_duplicate()


@pytest.mark.django_db
def test_azure_devops_configuration__soft_deleted__hidden_from_default_manager(
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    azure_devops_configuration.delete()

    # When
    visible_qs = AzureDevOpsConfiguration.objects.filter(project=project)
    all_qs = AzureDevOpsConfiguration.objects.all_with_deleted().filter(project=project)

    # Then
    assert not visible_qs.exists()
    assert all_qs.exists()
    assert all_qs.get().pk == azure_devops_configuration.pk
