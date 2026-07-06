from integrations.amplitude.models import AmplitudeConfiguration
from integrations.common.models import IntegrationHealthRecord
from integrations.common.services import record_integration_health


def test_record_integration_health__valid_integration_config__creates_health_record(
    environment,
):  # type: ignore[no-untyped-def]
    # Given
    amplitude_config = AmplitudeConfiguration.objects.create(
        api_key="test_amplitude",
        environment=environment,
    )
    status_code = 200

    # When
    record_integration_health(amplitude_config, status_code)

    # Then
    health_record = IntegrationHealthRecord.objects.get()
    assert health_record.content_object == amplitude_config
    assert health_record.status_code == status_code