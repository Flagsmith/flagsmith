from unittest.mock import MagicMock

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
    # Given ClickHouse settings unconfigured
    settings.CLICKHOUSE_ENABLED = False
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")

    # When the task runs
    backfill_identities_to_clickhouse()

    # Then it short-circuits without opening a cursor
    spy.assert_not_called()
    assert any(e["event"] == "backfill.skipped" for e in log.events)


def test_backfill_identities_to_clickhouse__dynamo_disabled__skips(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given ClickHouse configured but Dynamo wrapper disabled
    settings.CLICKHOUSE_ENABLED = True
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")
    mocker.patch.object(
        tasks,
        "DynamoIdentityWrapper",
        return_value=MagicMock(is_enabled=False),
    )

    # When the task runs
    backfill_identities_to_clickhouse()

    # Then it skips without opening a cursor
    spy.assert_not_called()


def test_backfill_identities_to_clickhouse__happy_path__bulk_inserts(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
    log: StructuredLogCapture,
) -> None:
    # Given a project with a canonical segment and a Dynamo wrapper
    # yielding two identities for its environment
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    cursor = MagicMock()
    open_cursor = mocker.patch.object(tasks, "open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    refresh_dispatch = mocker.patch.object(tasks, "refresh_project_segment_counts")
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
            },
            {
                "identity_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "identifier": "b",
                "composite_key": "k2",
                "environment_api_key": environment.api_key,
                "created_date": "2026-05-08T00:00:00Z",
                "identity_traits": [],
            },
        ]
    )
    mocker.patch.object(tasks, "DynamoIdentityWrapper", return_value=wrapper)

    # When the task runs
    backfill_identities_to_clickhouse()

    # Then ReplacingMergeTree handles dedup — no DELETE, just one bulk
    # INSERT for the two identities. The cursor is opened with the
    # per-(org, project) log_comment for spend attribution.
    open_cursor.assert_called_with(
        log_comment=(
            f"flagsmith:segment_membership:backfill"
            f":org_{project.organisation_id}"
            f":project_{project.id}"
        )
    )
    cursor.executemany.assert_called_once()
    sql, rows_arg = cursor.executemany.call_args.args
    assert sql == (
        "INSERT INTO IDENTITIES "
        "(environment_id, identifier, identity_key, traits) VALUES"
    )
    assert {row[0] for row in rows_arg} == {environment.api_key}
    assert {row[1] for row in rows_arg} == {"a", "b"}
    assert any(
        e["event"] == "backfill.environment.completed" and e["rows__count"] == 2
        for e in log.events
    )
    # And a per-project count refresh is dispatched once the backfill
    # finishes.
    refresh_dispatch.delay.assert_called_once_with(args=(project.id,))


def test_backfill_identities_to_clickhouse__insert_fails__logs_and_continues(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
    log: StructuredLogCapture,
) -> None:
    # Given the bulk insert blows up mid-batch
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

    # When the task runs
    backfill_identities_to_clickhouse()

    # Then the failure is logged and the loop continues
    assert any(e["event"] == "backfill.environment.failed" for e in log.events)


def test_backfill_identities_to_clickhouse__multiple_projects__fans_out_refresh_per_project(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    project_b: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given two FoF-enabled projects with canonical segments
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

    # When the backfill runs
    backfill_identities_to_clickhouse()

    # Then a per-project refresh is dispatched for each project we
    # actually processed (deduped) — once per project, not once per env
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
    # Given ClickHouse unconfigured
    settings.CLICKHOUSE_ENABLED = False
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")

    # When the per-project task runs
    refresh_project_segment_counts(project.id)

    # Then it short-circuits without opening a cursor
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
    # Given ClickHouse configured but FoF flag off (default)
    settings.CLICKHOUSE_ENABLED = True
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")

    # When the per-project task runs
    refresh_project_segment_counts(project.id)

    # Then it skips without opening a cursor
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
    # Given a project where count compute throws
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    cursor = MagicMock()
    open_cursor = mocker.patch.object(tasks, "open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    mocker.patch.object(
        tasks, "compute_segment_counts_for_project", side_effect=RuntimeError("boom")
    )

    # When the per-project task runs
    refresh_project_segment_counts(project.id)

    # Then the failure is logged
    assert any(e["event"] == "refresh.project.failed" for e in log.events)


def test_refresh_project_segment_counts__counts_returned__upserts_per_env_rows(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a project with a canonical segment and stubbed compute
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    cursor = MagicMock()
    open_cursor = mocker.patch.object(tasks, "open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    mocker.patch.object(
        tasks,
        "compute_segment_counts_for_project",
        return_value=[
            SegmentMembershipCount(
                segment_id=segment.id,
                environment_id=environment.id,
                count=42,
            ),
        ],
    )

    # When the per-project task runs
    refresh_project_segment_counts(project.id)

    # Then a SegmentMembershipCount row exists keyed by (segment, environment)
    membership = SegmentMembershipCount.objects.get(
        segment=segment, environment=environment
    )
    assert membership.count == 42
    assert membership.last_synced_at is not None

    # ...and the cursor was opened with a per-(org, project) log_comment so
    # the refresh's CH spend attributes cleanly.
    open_cursor.assert_called_once_with(
        log_comment=(
            f"flagsmith:segment_membership:refresh"
            f":org_{project.organisation_id}"
            f":project_{project.id}"
        )
    )
