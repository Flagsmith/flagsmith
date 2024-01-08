from environments.dynamodb import DynamoEnvironmentAPIKeyWrapper
from environments.models import EnvironmentAPIKey
from util.mappers import (
    map_environment_api_key_to_environment_api_key_document,
)


def test_write_api_keys_calls_internal_methods_correctly(
    mocker, environment, environment_api_key
):
    # Given
    dynamo_environment_api_key_wrapper = DynamoEnvironmentAPIKeyWrapper()
    mocked_dynamo_table = mocker.patch.object(
        dynamo_environment_api_key_wrapper, "_table"
    )

    expected_environment_api_key_document = (
        map_environment_api_key_to_environment_api_key_document(environment_api_key)
    )
    api_keys = EnvironmentAPIKey.objects.filter(id=environment_api_key.id)

    # When
    dynamo_environment_api_key_wrapper.write_api_keys(api_keys)

    # Then
    mocked_dynamo_table.batch_writer.assert_called_with()

    mocked_put_item = (
        mocked_dynamo_table.batch_writer.return_value.__enter__.return_value.put_item
    )
    _, kwargs = mocked_put_item.call_args
    actual_environment_api_key_document = kwargs["Item"]

    assert actual_environment_api_key_document == expected_environment_api_key_document


def test_write_api_key_calls_internal_methods_correctly(
    mocker, environment, environment_api_key
):
    # Given
    dynamo_environment_api_key_wrapper = DynamoEnvironmentAPIKeyWrapper()
    mocked_write_api_keys = mocker.patch.object(
        dynamo_environment_api_key_wrapper, "write_api_keys", autospec=True
    )

    # When
    dynamo_environment_api_key_wrapper.write_api_key(environment_api_key)

    # Then
    mocked_write_api_keys.assert_called_with([environment_api_key])
