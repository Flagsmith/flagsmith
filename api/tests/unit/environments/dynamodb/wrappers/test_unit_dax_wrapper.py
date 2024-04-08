from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.dynamodb.wrappers.base import BaseDynamoWrapper, DAXWrapper


def test_get_item_falls_back_to_dynamo_if_dax_raises_any_exception(
    mocker: MockerFixture, settings: SettingsWrapper
):
    # Given
    settings.DAX_ENDPOINT = "dax://test"
    dax_wrapper = DAXWrapper()
    expected_document = {"key": "value"}
    mocked_dynamo_table = mocker.patch.object(dax_wrapper, "_table")
    mocked_dax_table = mocker.patch.object(dax_wrapper, "_dax_table")

    mocked_dax_table.get_item.side_effect = Exception("DAX is down")
    mocked_dynamo_table.get_item.return_value = expected_document
    api_key = "test_key"

    # When
    returned_item = dax_wrapper.get_item({"api_key": api_key})

    # Then
    mocked_dax_table.get_item.assert_called_with(Key={"api_key": api_key})
    assert returned_item == expected_document
    mocked_dynamo_table.get_item.assert_called_with(Key={"api_key": api_key})


def test_delete_item_falls_back_to_dynamo_if_dax_raises_any_exception(
    mocker: MockerFixture, settings: SettingsWrapper
):
    # Given
    settings.DAX_ENDPOINT = "dax://test"
    dax_wrapper = DAXWrapper()
    mocked_dynamo_table = mocker.patch.object(dax_wrapper, "_table")
    mocked_dax_table = mocker.patch.object(dax_wrapper, "_dax_table")

    mocked_dax_table.delete_item.side_effect = Exception("DAX is down")
    api_key = "test_key"

    # When
    dax_wrapper.delete_item({"api_key": api_key})

    # Then
    mocked_dax_table.delete_item.assert_called_with(Key={"api_key": api_key})
    mocked_dynamo_table.delete_item.assert_called_with(Key={"api_key": api_key})


def test_batch_write_falls_back_to_dynamo_if_dax_raises_any_exception(
    mocker: MockerFixture, settings: SettingsWrapper
):
    # Given
    settings.DAX_ENDPOINT = "dax://test"
    dax_wrapper = DAXWrapper()
    mocked_dynamo_batch_write = mocker.patch.object(BaseDynamoWrapper, "batch_write")
    mocked_dax_table = mocker.patch.object(dax_wrapper, "_dax_table")

    mocked_dax_table.batch_writer.side_effect = Exception("DAX is down")
    items = [{"api_key": "test_key"}]

    # When
    dax_wrapper.batch_write(items)

    # Then
    mocked_dynamo_batch_write.assert_called_with(items)


def test_batch_write_calls_internal_methods_with_correct_arguments(
    mocker: MockerFixture, settings: SettingsWrapper
):
    # Given
    settings.DAX_ENDPOINT = "dax://test"
    dax_wrapper = DAXWrapper()
    mocked_dynamo_batch_write = mocker.patch.object(BaseDynamoWrapper, "batch_write")
    mocked_dax_table = mocker.patch.object(dax_wrapper, "_dax_table")

    items = [{"api_key": "test_key"}]

    # When
    dax_wrapper.batch_write(items)

    # Then

    mocked_dax_table.batch_writer.assert_called_with()
    mocked_dynamo_batch_write.assert_not_called()
    mocked_put_item = (
        mocked_dax_table.batch_writer.return_value.__enter__.return_value.put_item
    )
    _, kwargs = mocked_put_item.call_args
    actual_document = kwargs["Item"]

    assert actual_document == items[0]
