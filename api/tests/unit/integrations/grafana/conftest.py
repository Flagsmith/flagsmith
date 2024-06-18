import pytest

from integrations.grafana.models import GrafanaConfiguration


@pytest.fixture()
def deleted_grafana_configuration(project):
    configuration = GrafanaConfiguration.objects.create(
        project=project, base_url="http://localhost:3001", api_key="some-key"
    )
    configuration.delete()
    return configuration
