import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.dynamodb.types import IdentityOverridesV2Changeset
from environments.models import Environment
from features.models import Feature
from projects.models import IdentityOverridesV2MigrationStatus, Project
from projects.tasks import (
    handle_cascade_delete,
    migrate_project_environments_to_v2,
)
from segments.models import Segment
from task_processor.task_run_method import TaskRunMethod


@pytest.fixture
def project_v2_migration_in_progress(
    project: Project,
) -> Project:
    project.identity_overrides_v2_migration_status = (
        IdentityOverridesV2MigrationStatus.IN_PROGRESS
    )
    project.save()
    return project


@pytest.mark.parametrize(
    "migrate_environments_to_v2_return_value, expected_status",
    (
        (
            IdentityOverridesV2Changeset(to_put=[], to_delete=[]),
            IdentityOverridesV2MigrationStatus.COMPLETE,
        ),
        (
            None,
            IdentityOverridesV2MigrationStatus.IN_PROGRESS,
        ),
    ),
)
def test_migrate_project_environments_to_v2__calls_expected(
    mocker: MockerFixture,
    project_v2_migration_in_progress: Project,
    migrate_environments_to_v2_return_value: IdentityOverridesV2Changeset | None,
    expected_status: str,
):
    # Given
    mocked_migrate_environments_to_v2 = mocker.patch(
        "environments.dynamodb.services.migrate_environments_to_v2",
        autospec=True,
        return_value=None,
    )
    mocked_migrate_environments_to_v2.return_value = (
        migrate_environments_to_v2_return_value
    )

    # When
    migrate_project_environments_to_v2(project_id=project_v2_migration_in_progress.id)

    # Then
    project_v2_migration_in_progress.refresh_from_db()
    mocked_migrate_environments_to_v2.assert_called_once_with(
        project_id=project_v2_migration_in_progress.id,
    )
    assert (
        project_v2_migration_in_progress.identity_overrides_v2_migration_status
        == expected_status
    )


def test_migrate_project_environments_to_v2__expected_status_on_error(
    mocker: MockerFixture,
    project_v2_migration_in_progress: Project,
):
    # Given
    project_v2_migration_in_progress.identity_overrides_v2_migration_status = (
        IdentityOverridesV2MigrationStatus.IN_PROGRESS
    )

    mocked_migrate_environments_to_v2 = mocker.patch(
        "environments.dynamodb.services.migrate_environments_to_v2",
        autospec=True,
        side_effect=Exception,
    )

    # When
    with pytest.raises(Exception):
        migrate_project_environments_to_v2(
            project_id=project_v2_migration_in_progress.id
        )

    # Then
    mocked_migrate_environments_to_v2.assert_called_once_with(
        project_id=project_v2_migration_in_progress.id
    )
    assert project_v2_migration_in_progress.identity_overrides_v2_migration_status == (
        IdentityOverridesV2MigrationStatus.IN_PROGRESS
    )


def test_handle_cascade_delete(
    project: Project,
    environment: Environment,
    feature: Feature,
    segment: Segment,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY

    # When
    handle_cascade_delete(project_id=project.id)

    # Then
    assert not Environment.objects.filter(id=environment.id).exists()
    assert not Feature.objects.filter(id=feature.id).exists()
    assert not Segment.objects.filter(id=segment.id).exists()
