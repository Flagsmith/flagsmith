import pytest

from integrations.amplitude.models import AmplitudeConfiguration


@pytest.fixture()
def deleted_amplitude_integration(environment):  # type: ignore[no-untyped-def]
    amplitude_configuration = AmplitudeConfiguration.objects.create(
        environment=environment, api_key="some-key"
    )
    amplitude_configuration.delete()
    return amplitude_configuration
