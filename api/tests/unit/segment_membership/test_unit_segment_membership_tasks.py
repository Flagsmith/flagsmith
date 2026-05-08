from unittest.mock import MagicMock

from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.models import Environment
from projects.models import Project
from segment_membership import tasks
from segment_membership.models import SegmentMembership
from segment_membership.tasks import (
    backfill_identities_to_snowflake,
    refresh_project_segment_counts,
)
from segments.models import Segment
from tests.types import EnableFeaturesFixture


def test_backfill_identities_to_snowflake__no_snowflake_creds__skips(
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given Snowflake settings unconfigured
    mocker.patch.object(tasks, "is_snowflake_configured", return_value=False)
    spy = mocker.patch.object(tasks, "open_snowflake_session")

    # When the task runs
    backfill_identities_to_snowflake()

    # Then it short-circuits without opening a session
    spy.assert_not_called()
    assert any(e["event"] == "backfill.skipped" for e in log.events)


def test_backfill_identities_to_snowflake__dynamo_disabled__skips(
    mocker: MockerFixture,
) -> None:
    # Given Snowflake configured but Dynamo wrapper disabled
    mocker.patch.object(tasks, "is_snowflake_configured", return_value=True)
    spy = mocker.patch.object(tasks, "open_snowflake_session")
    mocker.patch.object(
        tasks,
        "DynamoIdentityWrapper",
        return_value=MagicMock(is_enabled=False),
    )

    # When the task runs
    backfill_identities_to_snowflake()

    # Then it skips without opening a session
    spy.assert_not_called()


def test_backfill_identities_to_snowflake__happy_path__deletes_then_inserts(
    mocker: MockerFixture,
    project: Project,
    environment: Environment,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
    log: StructuredLogCapture,
) -> None:
    # Given a project with a canonical segment and a Dynamo wrapper
    # yielding two identities for its environment
    enable_features("segment_membership_inspection")
    mocker.patch.object(tasks, "is_snowflake_configured", return_value=True)
    sess = MagicMock()
    mocker.patch.object(
        tasks, "open_snowflake_session"
    ).return_value.__enter__.return_value = sess
    refresh_dispatch = mocker.patch.object(tasks, "refresh_project_segment_counts")
    wrapper = MagicMock(is_enabled=True)
    wrapper.iter_all_items_paginated.return_value = iter(
        [
            {
                "identity_uuid": "u-1",
                "identifier": "a",
                "composite_key": "k1",
                "environment_api_key": environment.api_key,
                "created_date": "2026-05-08T00:00:00Z",
                "identity_traits": [],
            },
            {
                "identity_uuid": "u-2",
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
    backfill_identities_to_snowflake()

    # Then DELETE binds the env api key as a parameter and the identities
    # are written via the Snowpark DataFrame writer
    delete_calls = [
        call
        for call in sess.sql.call_args_list
        if call.args and call.args[0].startswith("DELETE FROM IDENTITIES")
    ]
    assert len(delete_calls) == 1
    assert delete_calls[0].kwargs == {"params": [environment.api_key]}

    sess.create_dataframe.assert_called_once()
    rows_arg = sess.create_dataframe.call_args.args[0]
    assert {row[0] for row in rows_arg} == {environment.api_key}
    assert {row[2] for row in rows_arg} == {"a", "b"}
    sess.create_dataframe.return_value.write.mode.assert_called_once_with("append")
    sess.create_dataframe.return_value.write.mode.return_value.save_as_table.assert_called_once_with(
        "IDENTITIES"
    )
    assert any(
        e["event"] == "backfill.environment.completed" and e["rows__count"] == 2
        for e in log.events
    )
    # And a per-project count refresh is dispatched once the backfill
    # finishes.
    refresh_dispatch.delay.assert_called_once_with(args=(project.id,))


def test_backfill_identities_to_snowflake__insert_fails__logs_and_continues(
    mocker: MockerFixture,
    project: Project,
    environment: Environment,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
    log: StructuredLogCapture,
) -> None:
    # Given the DataFrame write blows up mid-batch
    enable_features("segment_membership_inspection")
    mocker.patch.object(tasks, "is_snowflake_configured", return_value=True)
    sess = MagicMock()
    sess.create_dataframe.side_effect = RuntimeError("boom")
    mocker.patch.object(
        tasks, "open_snowflake_session"
    ).return_value.__enter__.return_value = sess
    wrapper = MagicMock(is_enabled=True)
    wrapper.iter_all_items_paginated.return_value = iter(
        [
            {
                "identity_uuid": "u-1",
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
    backfill_identities_to_snowflake()

    # Then the failure is logged and the loop continues
    assert any(e["event"] == "backfill.environment.failed" for e in log.events)


def test_backfill_identities_to_snowflake__multiple_projects__fans_out_refresh_per_project(
    mocker: MockerFixture,
    project: Project,
    project_b: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given two FoF-enabled projects with canonical segments
    enable_features("segment_membership_inspection")
    Segment.objects.create(name="seg-b", project=project_b)
    mocker.patch.object(tasks, "is_snowflake_configured", return_value=True)
    sess = MagicMock()
    mocker.patch.object(
        tasks, "open_snowflake_session"
    ).return_value.__enter__.return_value = sess
    refresh_dispatch = mocker.patch.object(tasks, "refresh_project_segment_counts")
    wrapper = MagicMock(is_enabled=True)
    wrapper.iter_all_items_paginated.return_value = iter([])
    mocker.patch.object(tasks, "DynamoIdentityWrapper", return_value=wrapper)

    # When the backfill runs
    backfill_identities_to_snowflake()

    # Then a per-project refresh is dispatched for each project we
    # actually processed (deduped) — once per project, not once per env
    dispatched_ids = {
        call.kwargs["args"][0] for call in refresh_dispatch.delay.call_args_list
    }
    assert dispatched_ids == {project.id, project_b.id}


def test_refresh_project_segment_counts__no_snowflake_creds__skips(
    mocker: MockerFixture,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given Snowflake unconfigured
    mocker.patch.object(tasks, "is_snowflake_configured", return_value=False)
    spy = mocker.patch.object(tasks, "open_snowflake_session")

    # When the per-project task runs
    refresh_project_segment_counts(project.id)

    # Then it short-circuits without opening a session
    spy.assert_not_called()
    assert any(
        e["event"] == "refresh.project.skipped"
        and e["reason"] == "snowflake_not_configured"
        for e in log.events
    )


def test_refresh_project_segment_counts__ff_disabled__skips(
    mocker: MockerFixture,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given Snowflake configured but FoF flag off (default)
    mocker.patch.object(tasks, "is_snowflake_configured", return_value=True)
    spy = mocker.patch.object(tasks, "open_snowflake_session")

    # When the per-project task runs
    refresh_project_segment_counts(project.id)

    # Then it skips without opening a session
    spy.assert_not_called()
    assert any(
        e["event"] == "refresh.project.skipped" and e["reason"] == "ff_disabled"
        for e in log.events
    )


def test_refresh_project_segment_counts__compute_fails__logs(
    mocker: MockerFixture,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
    log: StructuredLogCapture,
) -> None:
    # Given a project where count compute throws
    enable_features("segment_membership_inspection")
    mocker.patch.object(tasks, "is_snowflake_configured", return_value=True)
    sess = MagicMock()
    mocker.patch.object(
        tasks, "open_snowflake_session"
    ).return_value.__enter__.return_value = sess
    mocker.patch.object(
        tasks, "compute_segment_counts_for_project", side_effect=RuntimeError("boom")
    )

    # When the per-project task runs
    refresh_project_segment_counts(project.id)

    # Then the failure is logged
    assert any(e["event"] == "refresh.project.failed" for e in log.events)


def test_refresh_project_segment_counts__counts_returned__upserts_per_env_rows(
    mocker: MockerFixture,
    project: Project,
    environment: Environment,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a project with a canonical segment and stubbed compute
    enable_features("segment_membership_inspection")
    mocker.patch.object(tasks, "is_snowflake_configured", return_value=True)
    sess = MagicMock()
    mocker.patch.object(
        tasks, "open_snowflake_session"
    ).return_value.__enter__.return_value = sess
    mocker.patch.object(
        tasks,
        "compute_segment_counts_for_project",
        return_value=[
            SegmentMembership(
                segment_id=segment.id,
                environment_id=environment.id,
                count=42,
            ),
        ],
    )

    # When the per-project task runs
    refresh_project_segment_counts(project.id)

    # Then a SegmentMembership row exists keyed by (segment, environment)
    membership = SegmentMembership.objects.get(segment=segment, environment=environment)
    assert membership.count == 42
    assert membership.last_synced_at is not None
