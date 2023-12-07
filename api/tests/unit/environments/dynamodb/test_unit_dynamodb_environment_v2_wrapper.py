from pytest_django.fixtures import SettingsWrapper

from environments.dynamodb.dynamodb_wrapper import DynamoEnvironmentV2Wrapper
from environments.models import Environment


def test_environment_v2_wrapper_get_identity_overrides(
    settings: SettingsWrapper, environment: Environment
) -> None:
    # Given
    settings.ENVIRONMENTS_V2_TABLE_NAME_DYNAMO = "flagsmith_environments_v2"
    wrapper = DynamoEnvironmentV2Wrapper()

    # When
    results = wrapper.get_identity_overrides(environment_id=1)

    # Then
    assert results
