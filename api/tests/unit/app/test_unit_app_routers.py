import pytest
from django.apps import apps
from django.db.models import Model
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from app.routers import (
    PrimaryReplicaRouter,
    ReplicaReadStrategy,
    TaskProcessorRouter,
    connection_check,
)
from users.models import FFAdminUser


def test_connection_check_to_default_database(db: None, reset_cache: None) -> None:
    # When
    connection_check_works = connection_check("default")

    # Then
    assert connection_check_works is True


def test_replica_router_db_for_read_with_one_offline_replica(
    db: None,
    settings: SettingsWrapper,
    mocker: MockerFixture,
    reset_cache: None,
) -> None:
    # Given
    settings.NUM_DB_REPLICAS = 4

    # Set unused cross regional db for testing non-inclusion.
    settings.NUM_CROSS_REGION_DB_REPLICAS = 2
    settings.REPLICA_READ_STRATEGY = ReplicaReadStrategy.DISTRIBUTED

    conn_patch = mocker.MagicMock()
    conn_patch.is_usable.side_effect = (False, True)
    create_connection_patch = mocker.patch(
        "app.routers.connections.create_connection", return_value=conn_patch
    )

    router = PrimaryReplicaRouter()

    # When
    result = router.db_for_read(FFAdminUser)  # type: ignore[no-untyped-call]

    # Then
    # Read strategy DISTRIBUTED is random, so just this is a check
    # against loading the primary or one of the cross region replicas
    assert result.startswith("replica_")

    # Check that the number of replica call counts is as expected.
    conn_call_count = 2
    assert create_connection_patch.call_count == conn_call_count
    assert conn_patch.is_usable.call_count == conn_call_count


def test_replica_router_db_for_read_with_local_offline_replicas(
    db: None,
    settings: SettingsWrapper,
    mocker: MockerFixture,
    reset_cache: None,
) -> None:
    # Given
    settings.NUM_DB_REPLICAS = 4

    # Use cross regional db for fallback after replicas.
    settings.NUM_CROSS_REGION_DB_REPLICAS = 2
    settings.REPLICA_READ_STRATEGY = ReplicaReadStrategy.DISTRIBUTED

    conn_patch = mocker.MagicMock()

    # All four replicas go offline and so does one of the cross
    # regional replica as well, before finally the last cross
    # region replica is finally connected to.
    conn_patch.is_usable.side_effect = (
        False,
        False,
        False,
        False,
        False,
        True,
    )
    create_connection_patch = mocker.patch(
        "app.routers.connections.create_connection", return_value=conn_patch
    )

    router = PrimaryReplicaRouter()

    # When
    result = router.db_for_read(FFAdminUser)  # type: ignore[no-untyped-call]

    # Then
    # Read strategy DISTRIBUTED is random, so just this is a check
    # against loading the primary or one of the cross region replicas
    assert result.startswith("cross_region_replica_")

    # Check that the number of replica call counts is as expected.
    conn_call_count = 6
    assert create_connection_patch.call_count == conn_call_count
    assert conn_patch.is_usable.call_count == conn_call_count


def test_replica_router_db_for_read_with_all_offline_replicas(
    db: None,
    settings: SettingsWrapper,
    mocker: MockerFixture,
    reset_cache: None,
) -> None:
    # Given
    settings.NUM_DB_REPLICAS = 4
    settings.NUM_CROSS_REGION_DB_REPLICAS = 2
    settings.REPLICA_READ_STRATEGY = ReplicaReadStrategy.DISTRIBUTED

    conn_patch = mocker.MagicMock()

    # All replicas go offline.
    conn_patch.is_usable.return_value = False
    create_connection_patch = mocker.patch(
        "app.routers.connections.create_connection", return_value=conn_patch
    )

    router = PrimaryReplicaRouter()

    # When
    result = router.db_for_read(FFAdminUser)  # type: ignore[no-untyped-call]

    # Then
    # Fallback to primary database if all replicas are offline.
    assert result == "default"

    # Check that the number of replica call counts is as expected.
    conn_call_count = 6
    assert create_connection_patch.call_count == conn_call_count
    assert conn_patch.is_usable.call_count == conn_call_count


def test_replica_router_db_with_sequential_read(
    db: None,
    settings: SettingsWrapper,
    mocker: MockerFixture,
    reset_cache: None,
) -> None:
    # Given
    settings.NUM_DB_REPLICAS = 100
    settings.NUM_CROSS_REGION_DB_REPLICAS = 2
    settings.REPLICA_READ_STRATEGY = ReplicaReadStrategy.SEQUENTIAL

    conn_patch = mocker.MagicMock()

    # First replica is offline, so must fall back to second one.
    conn_patch.is_usable.side_effect = (False, True)
    create_connection_patch = mocker.patch(
        "app.routers.connections.create_connection", return_value=conn_patch
    )

    router = PrimaryReplicaRouter()

    # When
    result = router.db_for_read(FFAdminUser)  # type: ignore[no-untyped-call]

    # Then
    # Fallback from first replica to second one.
    assert result == "replica_2"

    # Check that the number of replica call counts is as expected.
    conn_call_count = 2
    assert create_connection_patch.call_count == conn_call_count
    assert conn_patch.is_usable.call_count == conn_call_count


def test_replica_router_db_no_replicas(
    db: None,
    settings: SettingsWrapper,
    mocker: MockerFixture,
    reset_cache: None,
) -> None:
    # Given
    settings.NUM_DB_REPLICAS = 0
    settings.NUM_CROSS_REGION_DB_REPLICAS = 0

    conn_patch = mocker.MagicMock()

    # All replicas should be ignored.
    create_connection_patch = mocker.patch(
        "app.routers.connections.create_connection", return_value=conn_patch
    )

    router = PrimaryReplicaRouter()

    # When
    result = router.db_for_read(FFAdminUser)  # type: ignore[no-untyped-call]

    # Then
    # Should always use primary database.
    assert result == "default"
    conn_call_count = 0
    assert create_connection_patch.call_count == conn_call_count
    assert conn_patch.is_usable.call_count == conn_call_count


@pytest.mark.parametrize(
    "given_settings, expected",
    [
        ({"TASK_PROCESSOR_DATABASE_URL": "postgres://localhost:5432/db"}, True),
        ({"TASK_PROCESSOR_DATABASE_URL": None}, False),
        ({"TASK_PROCESSOR_DATABASE_NAME": "db"}, True),
        ({"TASK_PROCESSOR_DATABASE_NAME": None}, False),
    ],
)
def test_TaskProcessorRouter__checks_whether_is_enabled(
    settings: SettingsWrapper,
    given_settings: dict[str, None | str],
    expected: bool,
) -> None:
    # Given
    for key, value in given_settings.items():
        setattr(settings, key, value)

    # When
    router = TaskProcessorRouter()

    # Then
    assert router.is_enabled is expected


@pytest.mark.parametrize("model", apps.get_app_config("task_processor").get_models())
def test_TaskProcessorRouter__enabled__routes_queries_to_task_processor_database(
    mocker: MockerFixture,
    model: type[Model],
) -> None:
    # Given
    mocker.patch.object(TaskProcessorRouter, "is_enabled", new=True)

    # When
    router = TaskProcessorRouter()
    result = router.db_for_read(model)

    # Then
    assert result == "task_processor"


@pytest.mark.parametrize("model", apps.get_app_config("task_processor").get_models())
def test_TaskProcessorRouter__disabled__routes_queries_to_default_database(
    mocker: MockerFixture,
    model: type[Model],
) -> None:
    # Given
    mocker.patch.object(TaskProcessorRouter, "is_enabled", new=False)

    # When
    router = TaskProcessorRouter()
    result = router.db_for_read(model)

    # Then
    assert result is None
