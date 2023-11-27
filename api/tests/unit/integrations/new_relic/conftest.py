import pytest

from integrations.new_relic.models import NewRelicConfiguration


@pytest.fixture()
def deleted_newrelic_configuration(project):
    configuration = NewRelicConfiguration.objects.create(
        project=project, api_key="some-key"
    )
    configuration.delete()
    return configuration
