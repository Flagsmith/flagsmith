import pytest

from environments.models import Environment
from experimentation.models import WarehouseConnection, WarehouseType
from organisations.models import Organisation
from projects.models import Project
from tests.unit.experimentation.conftest import SetWarehousesFlagFixture


@pytest.mark.django_db()
@pytest.mark.usefixtures("saas_mode")
def test_environment_create__auto_connect_enabled__creates_warehouse_connection(
    organisation: Organisation,
    set_warehouses_flag: SetWarehousesFlagFixture,
) -> None:
    # Given
    set_warehouses_flag({"auto_connect_flagsmith": True})
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
@pytest.mark.usefixtures("saas_mode")
def test_environment_create__auto_connect_disabled__no_warehouse_connection(
    organisation: Organisation,
) -> None:
    # Given
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
