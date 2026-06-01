from pytest_mock import MockerFixture

from environments.models import Environment
from experimentation.models import WarehouseConnection, WarehouseType


def test_warehouse_connection__after_create__enqueues_ingestion_add_task(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_task = mocker.patch(
        "experimentation.models.add_environment_key_to_ingestion",
    )

    # When
    WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="warehouse",
    )

    # Then
    mock_task.delay.assert_called_once_with(
        kwargs={"environment_api_key": environment.api_key},
    )


def test_warehouse_connection__after_delete__enqueues_ingestion_delete_task(
    warehouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_task = mocker.patch(
        "experimentation.models.delete_environment_key_from_ingestion",
    )
    environment_api_key = warehouse_connection.environment.api_key

    # When
    warehouse_connection.delete()

    # Then
    mock_task.delay.assert_called_once_with(
        kwargs={"environment_api_key": environment_api_key},
    )
