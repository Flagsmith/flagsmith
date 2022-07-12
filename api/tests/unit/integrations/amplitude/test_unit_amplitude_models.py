from django.db.models import Q

from integrations.amplitude.models import AmplitudeConfiguration


def test_amplitude_configuration_save_writes_environment_to_dynamodb(
    environment, mocker
):
    """
    Test to verify that AmplitudeConfiguration's base model class works as expected
    """
    # Given
    amplitude_config = AmplitudeConfiguration(
        environment=environment, api_key="api-key", base_url="https://base.url.com"
    )
    mock_environment_model_class = mocker.patch(
        "integrations.common.models.Environment"
    )

    # When
    amplitude_config.save()

    # Then
    mock_environment_model_class.write_environments_to_dynamodb.assert_called_once_with(
        Q(id=environment.id)
    )
