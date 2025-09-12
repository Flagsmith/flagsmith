import pytest

from integrations.datadog.models import DataDogConfiguration


@pytest.fixture()
def deleted_datadog_configuration(project):  # type: ignore[no-untyped-def]
    configuration = DataDogConfiguration.objects.create(
        project=project, api_key="some-key"
    )
    configuration.delete()
    return configuration
