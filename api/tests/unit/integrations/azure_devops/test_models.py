import uuid as uuid_module

import pytest
from django.db.utils import IntegrityError

from integrations.azure_devops.models import (
    AzureDevOpsConfiguration,
    AzureDevOpsServiceHook,
)
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


@pytest.mark.django_db
def test_azure_devops_service_hook__create__persists_fields(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    ado_project_id = uuid_module.uuid4()
    subscription_id = uuid_module.uuid4()

    # When
    hook = AzureDevOpsServiceHook.objects.create(
        configuration=azure_devops_configuration,
        ado_project_id=ado_project_id,
        ado_project_name="My ADO Project",
        event_type="git.pullrequest.merged",
        subscription_id=subscription_id,
        secret="rotation-pad-32-bytes-of-urlsafe-junk",
    )

    # Then
    assert hook.configuration == azure_devops_configuration
    assert hook.ado_project_id == ado_project_id
    assert hook.event_type == "git.pullrequest.merged"
    assert hook.uuid is not None


@pytest.mark.django_db
def test_azure_devops_service_hook__duplicate_event__raises_integrity_error(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    ado_project_id = uuid_module.uuid4()
    AzureDevOpsServiceHook.objects.create(
        configuration=azure_devops_configuration,
        ado_project_id=ado_project_id,
        ado_project_name="Project",
        event_type="git.pullrequest.merged",
        subscription_id=uuid_module.uuid4(),
        secret="secret-a",
    )

    duplicate_kwargs = {
        "configuration": azure_devops_configuration,
        "ado_project_id": ado_project_id,
        "ado_project_name": "Project",
        "event_type": "git.pullrequest.merged",
        "subscription_id": uuid_module.uuid4(),
        "secret": "secret-b",
    }

    # When
    def create_duplicate() -> None:
        AzureDevOpsServiceHook.objects.create(**duplicate_kwargs)

    # Then
    with pytest.raises(IntegrityError):
        create_duplicate()


@pytest.mark.django_db
def test_azure_devops_service_hook__different_event_type__allowed(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    ado_project_id = uuid_module.uuid4()
    AzureDevOpsServiceHook.objects.create(
        configuration=azure_devops_configuration,
        ado_project_id=ado_project_id,
        ado_project_name="Project",
        event_type="git.pullrequest.merged",
        subscription_id=uuid_module.uuid4(),
        secret="s1",
    )

    # When
    second = AzureDevOpsServiceHook.objects.create(
        configuration=azure_devops_configuration,
        ado_project_id=ado_project_id,
        ado_project_name="Project",
        event_type="workitem.updated",
        subscription_id=uuid_module.uuid4(),
        secret="s2",
    )

    # Then
    assert second.event_type == "workitem.updated"
