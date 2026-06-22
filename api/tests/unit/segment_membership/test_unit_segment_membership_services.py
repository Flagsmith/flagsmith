from unittest.mock import MagicMock

from common.test_tools import RunTasksFixture
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project
from segment_membership.services import (
    compute_segment_counts_for_project,
    enqueue_membership_refresh,
    get_projects_to_process,
    is_membership_enabled,
)
from segment_membership.tasks import refresh_project_segment_counts
from segments.models import Segment, SegmentRule
from tests.types import EnableFeaturesFixture


def test_is_membership_enabled__flag_off__returns_false(
    organisation: Organisation,
) -> None:
    # Given / When
    # Then
    assert is_membership_enabled(organisation) is False


def test_is_membership_enabled__flag_on__returns_true(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")

    # When / Then
    assert is_membership_enabled(organisation) is True


def test_get_projects_to_process__no_canonical_segments__yields_nothing(
    project: Project,
) -> None:
    # Given / When
    # Then
    assert list(get_projects_to_process()) == []


def test_get_projects_to_process__ff_disabled__skips_organisation(
    project: Project,
    segment: Segment,
) -> None:
    # Given / When
    # Then
    assert list(get_projects_to_process()) == []


def test_get_projects_to_process__ff_enabled__yields_project(
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")

    # When / Then
    assert list(get_projects_to_process()) == [project]


def test_get_projects_to_process__multiple_segments_per_project__yields_project_once(
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    Segment.objects.create(name="another", project=project)

    # When / Then
    assert list(get_projects_to_process()) == [project]


def test_compute_segment_counts_for_project__no_segments__returns_empty(
    project: Project,
) -> None:
    # Given
    cursor = MagicMock()

    # When
    result = compute_segment_counts_for_project(project, cursor)

    # Then
    assert result == []
    cursor.execute.assert_not_called()


def test_compute_segment_counts_for_project__no_environments__returns_empty(
    project: Project,
    segment: Segment,
) -> None:
    # Given
    project.environments.all().delete()
    cursor = MagicMock()

    # When
    result = compute_segment_counts_for_project(project, cursor)

    # Then
    assert result == []
    cursor.execute.assert_not_called()


def test_compute_segment_counts_for_project__unknown_env_key_in_row__skips(
    project: Project,
    environment: Environment,
    segment: Segment,
    segment_rule: SegmentRule,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "segment_membership.services.translate_segment",
        return_value="TRUE",
    )
    cursor = MagicMock()
    cursor.fetchall.return_value = [(segment.id, "ghost-env", 99)]

    # When
    result = compute_segment_counts_for_project(project, cursor)

    # Then
    assert result == []


def test_compute_segment_counts_for_project__untranslatable_segment__skips(
    project: Project,
    environment: Environment,
    segment: Segment,
    segment_rule: SegmentRule,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "segment_membership.services.translate_segment",
        return_value=None,
    )
    cursor = MagicMock()

    # When
    result = compute_segment_counts_for_project(project, cursor)

    # Then
    assert result == []
    cursor.execute.assert_not_called()


def test_enqueue_membership_refresh__flag_on__enqueues_refresh(
    run_tasks: RunTasksFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    # an org with the flag on
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    mocker.patch("segment_membership.tasks.open_clickhouse_cursor")
    compute_segment_counts_for_project_mock = mocker.patch(
        "segment_membership.tasks.compute_segment_counts_for_project",
        return_value=[],
    )

    # When
    enqueue_membership_refresh(project)
    run_tasks(num_tasks=2)

    # Then
    # exactly one refresh runs, for the project
    compute_segment_counts_for_project_mock.assert_called_once_with(project, mocker.ANY)


def test_enqueue_membership_refresh__flag_off__does_not_enqueue(
    run_tasks: RunTasksFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
) -> None:
    # Given
    # the org's flag is off
    settings.CLICKHOUSE_ENABLED = True
    mocker.patch("segment_membership.tasks.open_clickhouse_cursor")
    compute_segment_counts_for_project_mock = mocker.patch(
        "segment_membership.tasks.compute_segment_counts_for_project",
        return_value=[],
    )

    # When
    enqueue_membership_refresh(project)
    run_tasks(num_tasks=1)

    # Then
    # no refresh runs
    compute_segment_counts_for_project_mock.assert_not_called()


def test_enqueue_membership_refresh__refresh_already_pending__debounces(
    run_tasks: RunTasksFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    # a refresh for the same project is already pending
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    mocker.patch("segment_membership.tasks.open_clickhouse_cursor")
    compute_segment_counts_for_project_mock = mocker.patch(
        "segment_membership.tasks.compute_segment_counts_for_project",
        return_value=[],
    )
    refresh_project_segment_counts.delay(args=(project.id,))

    # When
    enqueue_membership_refresh(project)
    run_tasks(num_tasks=2)

    # Then
    # the call did not enqueue a second refresh -- only the pending one ran
    compute_segment_counts_for_project_mock.assert_called_once_with(project, mocker.ANY)


def test_enqueue_membership_refresh__pending_for_other_project__still_enqueues(
    run_tasks: RunTasksFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    project_b: Project,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    # a refresh is pending for a different project only
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    mocker.patch("segment_membership.tasks.open_clickhouse_cursor")
    compute_segment_counts_for_project_mock = mocker.patch(
        "segment_membership.tasks.compute_segment_counts_for_project",
        return_value=[],
    )
    refresh_project_segment_counts.delay(args=(project_b.id,))

    # When
    enqueue_membership_refresh(project)
    run_tasks(num_tasks=3)

    # Then
    # the debounce is scoped per project: both refreshes run
    assert compute_segment_counts_for_project_mock.call_count == 2
    compute_segment_counts_for_project_mock.assert_has_calls(
        [mocker.call(project, mocker.ANY), mocker.call(project_b, mocker.ANY)],
        any_order=True,
    )
