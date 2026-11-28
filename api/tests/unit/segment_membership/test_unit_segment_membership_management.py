from typing import Any
from unittest.mock import MagicMock

import pytest
from django.core.management import CommandError, call_command
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project


@pytest.fixture
def mock_cursor() -> MagicMock:
    cursor = MagicMock()
    return cursor


@pytest.fixture
def mock_open_clickhouse_cursor(
    mocker: MockerFixture, mock_cursor: MagicMock
) -> MagicMock:
    mock = mocker.patch(
        "segment_membership.management.commands."
        "tombstone_traitless_identities.open_clickhouse_cursor"
    )
    mock.return_value.__enter__.return_value = mock_cursor
    return mock


@pytest.fixture
def mock_enqueue_membership_refresh(mocker: MockerFixture) -> MagicMock:
    return mocker.patch(
        "segment_membership.management.commands."
        "tombstone_traitless_identities.enqueue_membership_refresh"
    )


@pytest.fixture
def mock_organisation() -> MagicMock:
    return MagicMock(spec=Organisation, id=1)


@pytest.fixture
def mock_project(mock_organisation: MagicMock) -> MagicMock:
    return MagicMock(
        spec=Project,
        id=10,
        organisation=mock_organisation,
        organisation_id=mock_organisation.id,
    )


@pytest.fixture
def mock_environment(mock_project: MagicMock) -> MagicMock:
    return MagicMock(
        spec=Environment,
        id=100,
        api_key="env_api_key_test_123",
        project=mock_project,
        project_id=mock_project.id,
    )


def _mock_env_queryset(environments: list[MagicMock]) -> MagicMock:
    qs = MagicMock()
    qs.exists.return_value = len(environments) > 0
    qs.select_related.return_value = qs
    qs.order_by.return_value = qs
    qs.iterator.return_value = iter(environments)
    qs.__iter__.return_value = iter(environments)
    return qs


def test_tombstone_traitless_identities__both_org_and_env_provided__raises_command_error(
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    organisation_id = 1
    environment_id = 2

    # When / Then
    with pytest.raises(
        CommandError,
        match=r"(?i)not allowed with argument|mutually exclusive",
    ):
        call_command(
            "tombstone_traitless_identities",
            f"--organisation-id={organisation_id}",
            f"--environment-id={environment_id}",
        )


def test_tombstone_traitless_identities__non_existent_organisation_id__raises_command_error(
    mocker: MockerFixture,
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    non_existent_org_id = 999999
    mock_org_objects = mocker.patch("organisations.models.Organisation.objects")
    mock_org_objects.filter.return_value.exists.return_value = False

    # When / Then
    with pytest.raises(
        CommandError,
        match=f"Organisation with id {non_existent_org_id} does not exist",
    ):
        call_command(
            "tombstone_traitless_identities",
            f"--organisation-id={non_existent_org_id}",
        )


def test_tombstone_traitless_identities__non_existent_environment_id__raises_command_error(
    mocker: MockerFixture,
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    non_existent_env_id = 999999
    mock_env_objects = mocker.patch("environments.models.Environment.objects")
    mock_env_objects.filter.return_value.exists.return_value = False

    # When / Then
    with pytest.raises(
        CommandError,
        match=f"Environment with id {non_existent_env_id} does not exist",
    ):
        call_command(
            "tombstone_traitless_identities",
            f"--environment-id={non_existent_env_id}",
        )


def test_tombstone_traitless_identities__clickhouse_disabled__prints_warning_and_skips(
    settings: SettingsWrapper,
    capsys: pytest.CaptureFixture[str],
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = False

    # When
    call_command("tombstone_traitless_identities")

    # Then
    mock_open_clickhouse_cursor.assert_not_called()
    mock_enqueue_membership_refresh.assert_not_called()
    captured = capsys.readouterr()
    assert "ClickHouse is not enabled. Skipping." in captured.out


def test_tombstone_traitless_identities__dry_run__queries_count_and_skips_insert_and_recount(
    mocker: MockerFixture,
    mock_environment: MagicMock,
    settings: SettingsWrapper,
    capsys: pytest.CaptureFixture[str],
    mock_cursor: MagicMock,
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    mock_cursor.fetchone.return_value = (5,)
    mock_env_objects = mocker.patch("environments.models.Environment.objects")
    mock_env_objects.filter.return_value = _mock_env_queryset([mock_environment])

    # When
    call_command(
        "tombstone_traitless_identities",
        f"--environment-id={mock_environment.id}",
        "--dry-run",
    )

    # Then
    mock_open_clickhouse_cursor.assert_called_once_with(
        log_comment=(
            f"flagsmith:segment_membership:tombstone:"
            f"org_{mock_environment.project.organisation_id}:env_{mock_environment.id}"
        )
    )
    assert mock_cursor.execute.call_count == 1
    sizing_call = mock_cursor.execute.call_args_list[0]
    assert "SELECT count()" in sizing_call[0][0]
    assert sizing_call[0][1] == {"env_key": mock_environment.api_key}

    mock_enqueue_membership_refresh.assert_not_called()

    captured = capsys.readouterr()
    assert (
        f"[DRY RUN] Environment {mock_environment.id} ({mock_environment.api_key}): "
        f"5 traitless identities found." in captured.out
    )
    assert (
        "Summary: 1 environments scanned, 5 identities would be tombstoned, 0 projects queued for recount."
        in captured.out
    )


def test_tombstone_traitless_identities__execution_mode_with_traitless__executes_tombstone_and_enqueues_recount(
    mocker: MockerFixture,
    mock_environment: MagicMock,
    settings: SettingsWrapper,
    capsys: pytest.CaptureFixture[str],
    mock_cursor: MagicMock,
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    mock_cursor.fetchone.return_value = (10,)
    mock_env_objects = mocker.patch("environments.models.Environment.objects")
    mock_env_objects.filter.return_value = _mock_env_queryset([mock_environment])

    # When
    call_command(
        "tombstone_traitless_identities",
        f"--environment-id={mock_environment.id}",
    )

    # Then
    mock_open_clickhouse_cursor.assert_called_once_with(
        log_comment=(
            f"flagsmith:segment_membership:tombstone:"
            f"org_{mock_environment.project.organisation_id}:env_{mock_environment.id}"
        )
    )
    assert mock_cursor.execute.call_count == 2
    sizing_call = mock_cursor.execute.call_args_list[0]
    assert "SELECT count()" in sizing_call[0][0]
    assert sizing_call[0][1] == {"env_key": mock_environment.api_key}
    tombstone_call = mock_cursor.execute.call_args_list[1]
    assert "INSERT INTO IDENTITIES" in tombstone_call[0][0]
    assert "inserted_at + INTERVAL 1 SECOND" in tombstone_call[0][0]
    assert "empty(JSONAllPaths(traits))" in tombstone_call[0][0]
    assert tombstone_call[0][1] == {"env_key": mock_environment.api_key}

    mock_enqueue_membership_refresh.assert_called_once_with(mock_environment.project)

    captured = capsys.readouterr()
    assert (
        f"Environment {mock_environment.id} ({mock_environment.api_key}): "
        f"Tombstoning 10 traitless identities." in captured.out
    )
    assert (
        "Summary: 1 environments scanned, 10 identities tombstoned, 1 projects queued for recount."
        in captured.out
    )


def test_tombstone_traitless_identities__zero_traitless_count__does_not_execute_insert_nor_enqueue_recount(
    mocker: MockerFixture,
    mock_environment: MagicMock,
    settings: SettingsWrapper,
    capsys: pytest.CaptureFixture[str],
    mock_cursor: MagicMock,
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    mock_cursor.fetchone.return_value = (0,)
    mock_env_objects = mocker.patch("environments.models.Environment.objects")
    mock_env_objects.filter.return_value = _mock_env_queryset([mock_environment])

    # When
    call_command(
        "tombstone_traitless_identities",
        f"--environment-id={mock_environment.id}",
    )

    # Then
    mock_open_clickhouse_cursor.assert_called_once()
    assert mock_cursor.execute.call_count == 1
    assert "SELECT count()" in mock_cursor.execute.call_args_list[0][0][0]
    mock_enqueue_membership_refresh.assert_not_called()

    captured = capsys.readouterr()
    assert (
        "Summary: 1 environments scanned, 0 identities tombstoned, 0 projects queued for recount."
        in captured.out
    )


def test_tombstone_traitless_identities__skip_recount_flag__executes_tombstone_without_enqueueing_recount(
    mocker: MockerFixture,
    mock_environment: MagicMock,
    settings: SettingsWrapper,
    capsys: pytest.CaptureFixture[str],
    mock_cursor: MagicMock,
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    mock_cursor.fetchone.return_value = (7,)
    mock_env_objects = mocker.patch("environments.models.Environment.objects")
    mock_env_objects.filter.return_value = _mock_env_queryset([mock_environment])

    # When
    call_command(
        "tombstone_traitless_identities",
        f"--environment-id={mock_environment.id}",
        "--skip-recount",
    )

    # Then
    assert mock_cursor.execute.call_count == 2
    assert "INSERT INTO IDENTITIES" in mock_cursor.execute.call_args_list[1][0][0]
    mock_enqueue_membership_refresh.assert_not_called()

    captured = capsys.readouterr()
    assert (
        "Summary: 1 environments scanned, 7 identities tombstoned, 0 projects queued for recount."
        in captured.out
    )


def test_tombstone_traitless_identities__organisation_id_provided__processes_organisation_environments(
    mocker: MockerFixture,
    mock_organisation: MagicMock,
    mock_project: MagicMock,
    mock_environment: MagicMock,
    settings: SettingsWrapper,
    mock_cursor: MagicMock,
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    mock_cursor.fetchone.return_value = (8,)
    mock_org_objects = mocker.patch("organisations.models.Organisation.objects")
    mock_org_objects.filter.return_value.exists.return_value = True

    mock_env_objects = mocker.patch("environments.models.Environment.objects")
    mock_env_objects.filter.return_value = _mock_env_queryset([mock_environment])

    # When
    call_command(
        "tombstone_traitless_identities",
        f"--organisation-id={mock_organisation.id}",
    )

    # Then
    mock_org_objects.filter.assert_called_once_with(id=mock_organisation.id)
    mock_env_objects.filter.assert_called_once_with(
        project__organisation_id=mock_organisation.id
    )
    assert mock_open_clickhouse_cursor.call_count == 1
    mock_open_clickhouse_cursor.assert_called_once_with(
        log_comment=(
            f"flagsmith:segment_membership:tombstone:"
            f"org_{mock_organisation.id}:env_{mock_environment.id}"
        )
    )
    mock_enqueue_membership_refresh.assert_called_once_with(mock_project)


def test_tombstone_traitless_identities__default_scope__processes_only_seeded_organisations(
    mocker: MockerFixture,
    mock_organisation: MagicMock,
    mock_project: MagicMock,
    mock_environment: MagicMock,
    settings: SettingsWrapper,
    mock_cursor: MagicMock,
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    mock_cursor.fetchone.return_value = (3,)

    mock_seed_objects = mocker.patch(
        "segment_membership.models.SegmentMembershipSeed.objects"
    )
    seeded_qs = MagicMock()
    mock_seed_objects.filter.return_value = seeded_qs
    seeded_qs.values_list.return_value = [mock_organisation.id]

    mock_env_objects = mocker.patch("environments.models.Environment.objects")
    mock_env_objects.filter.return_value = _mock_env_queryset([mock_environment])

    # When
    call_command("tombstone_traitless_identities")

    # Then
    mock_seed_objects.filter.assert_called_once_with(seeded_at__isnull=False)
    seeded_qs.values_list.assert_called_once_with("organisation_id", flat=True)
    mock_env_objects.filter.assert_called_once_with(
        project__organisation_id__in=[mock_organisation.id]
    )
    assert mock_open_clickhouse_cursor.call_count == 1
    mock_open_clickhouse_cursor.assert_called_once_with(
        log_comment=(
            f"flagsmith:segment_membership:tombstone:"
            f"org_{mock_organisation.id}:env_{mock_environment.id}"
        )
    )
    mock_enqueue_membership_refresh.assert_called_once_with(mock_project)


def test_tombstone_traitless_identities__partial_failure__continues_processing_and_raises_command_error(
    mocker: MockerFixture,
    mock_organisation: MagicMock,
    mock_project: MagicMock,
    settings: SettingsWrapper,
    capsys: pytest.CaptureFixture[str],
    mock_cursor: MagicMock,
    mock_open_clickhouse_cursor: MagicMock,
    mock_enqueue_membership_refresh: MagicMock,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    env_1 = MagicMock(
        spec=Environment,
        id=101,
        api_key="env_api_key_1",
        project=mock_project,
        project_id=mock_project.id,
    )
    env_2 = MagicMock(
        spec=Environment,
        id=102,
        api_key="env_api_key_2",
        project=mock_project,
        project_id=mock_project.id,
    )

    mock_org_objects = mocker.patch("organisations.models.Organisation.objects")
    mock_org_objects.filter.return_value.exists.return_value = True

    mock_env_objects = mocker.patch("environments.models.Environment.objects")
    mock_env_objects.filter.return_value = _mock_env_queryset([env_1, env_2])

    mock_cursor.fetchone.return_value = (4,)

    class MockContextManager:
        def __init__(self, comment: str | None) -> None:
            self.comment = comment

        def __enter__(self) -> MagicMock:
            if f"env_{env_1.id}" in (self.comment or ""):
                raise RuntimeError("ClickHouse connection error")
            return mock_cursor

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: Any,
        ) -> None:
            pass

    mock_open_clickhouse_cursor.side_effect = lambda log_comment=None: (
        MockContextManager(log_comment)
    )

    # When / Then
    with pytest.raises(
        CommandError,
        match=f"Tombstoning failed for environment\\(s\\): \\[{env_1.id}\\]",
    ):
        call_command(
            "tombstone_traitless_identities",
            f"--organisation-id={mock_organisation.id}",
        )

    # Both environments were attempted
    assert mock_open_clickhouse_cursor.call_count == 2
    mock_enqueue_membership_refresh.assert_called_once_with(mock_project)
    captured = capsys.readouterr()
    assert (
        f"Failed processing environment {env_1.id}: ClickHouse connection error"
        in captured.err
    )
    assert (
        f"Environment {env_2.id} ({env_2.api_key}): Tombstoning 4 traitless identities."
        in captured.out
    )
