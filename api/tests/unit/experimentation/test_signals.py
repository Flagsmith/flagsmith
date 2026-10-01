import pytest
from pytest_mock import MockerFixture

from environments.models import Environment
from experimentation.models import WarehouseConnection, WarehouseType
from organisations.models import Organisation
from projects.models import Project


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
