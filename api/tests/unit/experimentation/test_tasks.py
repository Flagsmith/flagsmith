from pytest_mock import MockerFixture

from experimentation.tasks import (
    add_environment_key_to_ingestion,
    delete_environment_key_from_ingestion,
)


def test_add_environment_key_to_ingestion__valid_key__calls_service(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_set = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.set_environment_key",
    )

    # When
    add_environment_key_to_ingestion(environment_api_key="test-env-key-001")

    # Then
    mock_set.assert_called_once_with("test-env-key-001")


def test_delete_environment_key_from_ingestion__valid_key__calls_service(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_delete = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.delete_environment_key",
    )

    # When
    delete_environment_key_from_ingestion(environment_api_key="test-env-key-001")

    # Then
    mock_delete.assert_called_once_with("test-env-key-001")
