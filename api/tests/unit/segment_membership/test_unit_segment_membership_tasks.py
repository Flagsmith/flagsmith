from unittest.mock import MagicMock

from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.models import Environment
from projects.models import Project
from segment_membership import tasks
from segment_membership.models import SegmentMembershipCount
from segment_membership.tasks import (
    backfill_identities_to_clickhouse,
    refresh_project_segment_counts,
)
from segments.models import Segment
from tests.types import EnableFeaturesFixture


def test_backfill_identities_to_clickhouse__no_clickhouse_creds__skips(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = False
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")

    # When
    backfill_identities_to_clickhouse()

    # Then
    spy.assert_not_called()
    assert any(e["event"] == "backfill.skipped" for e in log.events)


def test_backfill_identities_to_clickhouse__dynamo_disabled__skips(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")
    mocker.patch.object(
        tasks,
        "DynamoIdentityWrapper",
        return_value=MagicMock(is_enabled=False),
    )

    # When
    backfill_identities_to_clickhouse()

    # Then
    spy.assert_not_called()


def test_backfill_identities_to_clickhouse__insert_fails__logs_and_continues(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    cursor = MagicMock()
    cursor.executemany.side_effect = RuntimeError("boom")
    open_cursor = mocker.patch.object(tasks, "open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    wrapper = MagicMock(is_enabled=True)
    wrapper.iter_all_items_paginated.return_value = iter(
        [
            {
                "identity_uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "identifier": "a",
                "composite_key": "k1",
                "environment_api_key": environment.api_key,
                "created_date": "2026-05-08T00:00:00Z",
                "identity_traits": [],
            }
        ]
    )
    mocker.patch.object(tasks, "DynamoIdentityWrapper", return_value=wrapper)

    # When
    backfill_identities_to_clickhouse()

    # Then
    assert any(e["event"] == "backfill.environment.failed" for e in log.events)


def test_backfill_identities_to_clickhouse__multiple_projects__fans_out_refresh_per_project(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    project_b: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    Segment.objects.create(name="seg-b", project=project_b)
    settings.CLICKHOUSE_ENABLED = True
    cursor = MagicMock()
    open_cursor = mocker.patch.object(tasks, "open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    refresh_dispatch = mocker.patch.object(tasks, "refresh_project_segment_counts")
    wrapper = MagicMock(is_enabled=True)
    wrapper.iter_all_items_paginated.return_value = iter([])
    mocker.patch.object(tasks, "DynamoIdentityWrapper", return_value=wrapper)

    # When
    backfill_identities_to_clickhouse()

    # Then
    dispatched_ids = {
        call.kwargs["args"][0] for call in refresh_dispatch.delay.call_args_list
    }
    assert dispatched_ids == {project.id, project_b.id}


def test_refresh_project_segment_counts__no_clickhouse_creds__skips(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = False
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")

    # When
    refresh_project_segment_counts(project.id)

    # Then
    spy.assert_not_called()
    assert any(
        e["event"] == "refresh.project.skipped"
        and e["reason"] == "clickhouse_not_configured"
        for e in log.events
    )


def test_refresh_project_segment_counts__ff_disabled__skips(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")

    # When
    refresh_project_segment_counts(project.id)

    # Then
    spy.assert_not_called()
    assert any(
        e["event"] == "refresh.project.skipped" and e["reason"] == "ff_disabled"
        for e in log.events
    )


def test_refresh_project_segment_counts__compute_fails__logs(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    cursor = MagicMock()
    open_cursor = mocker.patch.object(tasks, "open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    mocker.patch.object(
        tasks, "compute_segment_counts_for_project", side_effect=RuntimeError("boom")
    )

    # When
    refresh_project_segment_counts(project.id)

    # Then
    assert any(e["event"] == "refresh.project.failed" for e in log.events)


def test_refresh_project_segment_counts__previously_matching_pair_drops_to_zero__row_deleted(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a prior refresh that landed a non-zero count for (segment, env)
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    SegmentMembershipCount.objects.create(
        segment=segment,
        environment=environment,
        count=15,
        last_synced_at=timezone.now(),
    )
    cursor = MagicMock()
    open_cursor = mocker.patch.object(tasks, "open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    # ... and a new compute that returns no matches for the same pair (the
    # rule was edited, the identity set drifted, etc.).
    mocker.patch.object(tasks, "compute_segment_counts_for_project", return_value=[])

    # When
    refresh_project_segment_counts(project.id)

    # Then the stale row is gone -- pairs that no longer match drop out of
    # the table entirely rather than lingering at the previous count.
    assert not SegmentMembershipCount.objects.filter(
        segment=segment, environment=environment
    ).exists()


def test_refresh_project_segment_counts__never_matched_pair__no_row_written(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a project with no prior membership rows
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    cursor = MagicMock()
    open_cursor = mocker.patch.object(tasks, "open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    mocker.patch.object(tasks, "compute_segment_counts_for_project", return_value=[])

    # When
    refresh_project_segment_counts(project.id)

    # Then no row is written: refresh upserts matches, drops misses, and
    # leaves never-matched pairs untouched.
    assert not SegmentMembershipCount.objects.filter(
        segment=segment, environment=environment
    ).exists()
