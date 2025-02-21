from unittest.mock import call

import pytest
from _pytest.capture import CaptureFixture
from django.core.management import CommandError, call_command
from django.db.migrations.recorder import MigrationRecorder
from pytest_mock import MockerFixture


class MockQuerySet(list):  # type: ignore[type-arg]
    def exists(self) -> bool:
        return self.__len__() > 0


def test_rollbackmigrationsappliedafter(mocker: MockerFixture) -> None:
    # Given
    dt_string = "2024-10-24 08:23:45"

    migration_1 = mocker.MagicMock(app="foo", spec=MigrationRecorder.Migration)
    migration_1.name = "0001_initial"

    migration_2 = mocker.MagicMock(app="bar", spec=MigrationRecorder.Migration)
    migration_2.name = "0002_some_migration_description"

    migration_3 = mocker.MagicMock(app="bar", spec=MigrationRecorder.Migration)
    migration_3.name = "0003_some_other_migration_description"

    migrations = MockQuerySet([migration_1, migration_2, migration_3])

    mocked_migration_recorder = mocker.patch(
        "core.management.commands.rollbackmigrationsappliedafter.MigrationRecorder"
    )
    mocked_migration_recorder.Migration.objects.filter.return_value.order_by.return_value = migrations

    mocked_call_command = mocker.patch(
        "core.management.commands.rollbackmigrationsappliedafter.call_command"
    )

    # When
    call_command("rollbackmigrationsappliedafter", dt_string)

    # Then
    assert mocked_call_command.mock_calls == [
        call("migrate", "foo", "zero"),
        call("migrate", "bar", "0001"),
    ]


def test_rollbackmigrationsappliedafter_invalid_date(mocker: MockerFixture) -> None:
    # Given
    dt_string = "foo"

    mocked_call_command = mocker.patch(
        "core.management.commands.rollbackmigrationsappliedafter.call_command"
    )

    # When
    with pytest.raises(CommandError) as e:
        call_command("rollbackmigrationsappliedafter", dt_string)

    # Then
    assert mocked_call_command.mock_calls == []
    assert e.value.args == ("Date must be in ISO format",)


def test_rollbackmigrationsappliedafter_no_migrations(
    mocker: MockerFixture,
    capsys: CaptureFixture,  # type: ignore[type-arg]
) -> None:
    # Given
    dt_string = "2024-10-01"

    mocked_migration_recorder = mocker.patch(
        "core.management.commands.rollbackmigrationsappliedafter.MigrationRecorder"
    )
    mocked_migration_recorder.Migration.objects.filter.return_value.order_by.return_value = MockQuerySet(
        []
    )

    mocked_call_command = mocker.patch(
        "core.management.commands.rollbackmigrationsappliedafter.call_command"
    )

    # When
    call_command("rollbackmigrationsappliedafter", dt_string)

    # Then
    assert mocked_call_command.mock_calls == []

    captured = capsys.readouterr()
    assert captured.out == "No migrations to rollback.\n"
