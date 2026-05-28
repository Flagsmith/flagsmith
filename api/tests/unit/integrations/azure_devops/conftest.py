import pytest

from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.models import Project


@pytest.fixture()
def azure_devops_configuration(project: Project) -> AzureDevOpsConfiguration:
    return AzureDevOpsConfiguration.objects.create(  # type: ignore[no-any-return]
        project=project,
        organisation_url="https://dev.azure.com/test-org",
        personal_access_token="ado-test-token",
    )
