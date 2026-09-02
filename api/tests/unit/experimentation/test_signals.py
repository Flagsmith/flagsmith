import pytest
from pytest_mock import MockerFixture

from environments.models import Environment, EnvironmentAPIKey
from experimentation.models import WarehouseConnection, WarehouseType
from organisations.models import Organisation
from projects.models import Project


def test_environment_api_key__created_with_warehouse__enqueues_write(
    warehouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    environment = warehouse_connection.environment
    mock_task = mocker.patch(
        "experimentation.tasks.write_environment_ingestion_key",
    )

    # When
    api_key = EnvironmentAPIKey.objects.create(environment=environment, name="backend")

    # Then
    mock_task.delay.assert_called_once_with(
        kwargs={"environment_api_key_id": api_key.id},
    )


def test_environment_api_key__updated_with_warehouse__enqueues_write(
    warehouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    environment = warehouse_connection.environment
    api_key = EnvironmentAPIKey.objects.create(environment=environment, name="backend")
    mock_task = mocker.patch(
        "experimentation.tasks.write_environment_ingestion_key",
    )

    # When
    api_key.active = False
    api_key.save()

    # Then
    mock_task.delay.assert_called_once_with(
        kwargs={"environment_api_key_id": api_key.id},
    )


def test_environment_api_key__saved_without_warehouse__does_not_enqueue(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_task = mocker.patch(
        "experimentation.tasks.write_environment_ingestion_key",
    )

    # When
    EnvironmentAPIKey.objects.create(environment=environment, name="backend")

    # Then
    mock_task.delay.assert_not_called()


def test_environment_api_key__deleted_with_warehouse__enqueues_removal(
    warehouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    environment = warehouse_connection.environment
    api_key = EnvironmentAPIKey.objects.create(environment=environment, name="backend")
    key = api_key.key
    mock_task = mocker.patch(
        "experimentation.tasks.remove_environment_ingestion_key",
    )

    # When
    api_key.delete()

    # Then
    mock_task.delay.assert_called_once_with(kwargs={"key": key})


def test_environment_api_key__deleted_without_warehouse__does_not_enqueue(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    api_key = EnvironmentAPIKey.objects.create(environment=environment, name="backend")
    mock_task = mocker.patch(
        "experimentation.tasks.remove_environment_ingestion_key",
    )

    # When
    api_key.delete()

    # Then
    mock_task.delay.assert_not_called()


@pytest.mark.django_db()
def test_environment_create__auto_connect_enabled__creates_warehouse_connection(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "experimentation.services.get_experiment_flag_config",
        return_value={"auto_connect_warehouse": True},
    )
    project: Project = Project.objects.create(
        name="Test Project",
        organisation=organisation,
    )

    # When
    environment: Environment = Environment.objects.create(
        name="Test Environment",
        project=project,
    )

    # Then
    connection = WarehouseConnection.objects.get(environment=environment)
    assert connection.warehouse_type == WarehouseType.FLAGSMITH
    assert connection.name == "Flagsmith"


@pytest.mark.django_db()
def test_environment_create__auto_connect_disabled__no_warehouse_connection(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "experimentation.services.get_experiment_flag_config",
        return_value={},
    )
    project: Project = Project.objects.create(
        name="Test Project",
        organisation=organisation,
    )

    # When
    environment: Environment = Environment.objects.create(
        name="Test Environment",
        project=project,
    )

    # Then
    assert not WarehouseConnection.objects.filter(environment=environment).exists()
