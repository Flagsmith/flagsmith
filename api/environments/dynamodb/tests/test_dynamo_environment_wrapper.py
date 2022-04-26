from flag_engine.api.document_builders import build_environment_document

from environments.dynamodb import DynamoEnvironmentWrapper
from environments.models import Environment


def test_write_environments_calls_internal_methods_with_correct_arguments(
    mocker, project, environment
):
    # Given
    dynamo_environment_wrapper = DynamoEnvironmentWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_environment_wrapper, "_table")

    expected_environment_document = build_environment_document(environment)
    environments = Environment.objects.filter(id=environment.id)

    # When
    dynamo_environment_wrapper.write_environments(environments)

    # Then
    mocked_dynamo_table.batch_writer.assert_called_with()

    mocked_put_item = (
        mocked_dynamo_table.batch_writer.return_value.__enter__.return_value.put_item
    )
    _, kwargs = mocked_put_item.call_args
    actual_environment_document = kwargs["Item"]

    assert actual_environment_document == expected_environment_document
