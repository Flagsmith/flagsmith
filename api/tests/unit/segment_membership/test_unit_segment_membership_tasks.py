from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from unittest.mock import MagicMock

import pytest
from django.db import connections
from django.utils import timezone
from mypy_boto3_dynamodb.service_resource import Table
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from task_processor.models import Task
from task_processor.task_run_method import TaskRunMethod

from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project
from segment_membership import tasks
from segment_membership.models import SegmentMembershipCount, SegmentMembershipSeed
from segment_membership.tasks import (
    reconcile_segment_membership_seeds,
    refresh_all_segment_counts,
    refresh_project_segment_counts,
    seed_organisation_identities,
)
from segments.models import Segment
from tests.types import EnableFeaturesFixture

SCAN_START = datetime(2026, 6, 1, 12, 0, 0, tzinfo=dt_timezone.utc)


@pytest.fixture
def dynamo_identities(
    flagsmith_identities_table: Table,
    environment: Environment,
) -> None:
    for identifier, trait_value in (("alice", "bar"), ("carol", "baz")):
        flagsmith_identities_table.put_item(
            Item={
                "composite_key": f"{environment.api_key}_{identifier}",
                "environment_api_key": environment.api_key,
                "identifier": identifier,
                "identity_uuid": f"f47ac10b-58cc-4372-a567-0e02b2c3d47{identifier[0]}",
                "identity_traits": [{"trait_key": "foo", "trait_value": trait_value}],
            }
        )


def test_seed_organisation_identities__no_clickhouse_creds__skips(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = False
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")

    # When
    seed_organisation_identities(project.organisation_id)

    # Then
    spy.assert_not_called()
    assert log.events == [
        {
            "level": "warning",
            "event": "seed.skipped",
            "organisation__id": project.organisation_id,
            "reason": "clickhouse_not_configured",
        }
    ]


def test_seed_organisation_identities__dynamo_disabled__skips(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")
    mocker.patch.object(
        tasks,
        "DynamoIdentityWrapper",
        return_value=MagicMock(is_enabled=False),
    )

    # When
    seed_organisation_identities(project.organisation_id)

    # Then
    spy.assert_not_called()


def test_seed_organisation_identities__flag_off__skips(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")

    # When
    seed_organisation_identities(project.organisation_id)

    # Then
    spy.assert_not_called()
    assert not SegmentMembershipSeed.objects.filter(
        organisation=project.organisation, seeded_at__isnull=False
    ).exists()


def test_seed_organisation_identities__insert_fails__logs_and_continues(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
    segment: Segment,
    flagsmith_identities_table: Table,
    dynamo_identities: None,
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
    mocker.patch.object(tasks, "enqueue_membership_refresh")

    # When
    seed_organisation_identities(project.organisation_id)

    # Then
    assert log.events == [
        {
            "event": "seed.environment.failed",
            "level": "error",
            "exc_info": mocker.ANY,
            "organisation__id": project.organisation_id,
            "project__id": project.id,
            "environment__id": environment.id,
        }
    ]


@pytest.mark.clickhouse
def test_seed_organisation_identities__matching_identities__inserts_rows_versioned_at_scan_start(
    mocker: MockerFixture,
    clickhouse_db: None,
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
    segment: Segment,
    dynamo_identities: None,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    mocker.patch("segment_membership.tasks.timezone.now", return_value=SCAN_START)
    mocker.patch.object(tasks, "enqueue_membership_refresh")

    # When
    seed_organisation_identities(project.organisation_id)

    # Then
    with connections["clickhouse"].cursor() as cursor:
        cursor.execute(
            "SELECT identifier, identity_key, traits, inserted_at "
            "FROM IDENTITIES FINAL WHERE environment_id = %(key)s "
            "ORDER BY identifier",
            {"key": environment.api_key},
        )
        rows = cursor.fetchall()
    assert rows == [
        (
            "alice",
            f"{environment.api_key}_alice",
            {"foo": "bar"},
            SCAN_START.replace(tzinfo=None),
        ),
        (
            "carol",
            f"{environment.api_key}_carol",
            {"foo": "baz"},
            SCAN_START.replace(tzinfo=None),
        ),
    ]


@pytest.mark.clickhouse
def test_seed_organisation_identities__success__marks_org_seeded(
    mocker: MockerFixture,
    clickhouse_db: None,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    flagsmith_identities_table: Table,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    mocker.patch.object(tasks, "enqueue_membership_refresh")

    # When
    seed_organisation_identities(project.organisation_id)

    # Then
    assert SegmentMembershipSeed.objects.filter(
        organisation=project.organisation, seeded_at__isnull=False
    ).exists()


@pytest.mark.clickhouse
def test_seed_organisation_identities__success__fans_out_refresh_per_project(
    mocker: MockerFixture,
    clickhouse_db: None,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    flagsmith_identities_table: Table,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    project_b = Project.objects.create(
        name="project-b", organisation=project.organisation
    )
    Segment.objects.create(name="seg-b", project=project_b)
    settings.CLICKHOUSE_ENABLED = True
    enqueue = mocker.patch.object(tasks, "enqueue_membership_refresh")

    # When
    seed_organisation_identities(project.organisation_id)

    # Then
    dispatched_ids = {call.args[0].id for call in enqueue.call_args_list}
    assert dispatched_ids == {project.id, project_b.id}


def test_reconcile_segment_membership_seeds__no_clickhouse_creds__skips(
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = False

    # When
    reconcile_segment_membership_seeds()

    # Then
    assert not Task.objects.filter(
        task_identifier=seed_organisation_identities.task_identifier,
        serialized_args=Task.serialize_data((project.organisation_id,)),
    ).exists()


def test_reconcile_segment_membership_seeds__flagged_unseeded_org__enqueues_seed(
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR

    # When
    reconcile_segment_membership_seeds()

    # Then
    assert (
        Task.objects.filter(
            task_identifier=seed_organisation_identities.task_identifier,
            completed=False,
            serialized_args=Task.serialize_data((project.organisation_id,)),
        ).count()
        == 1
    )


def test_reconcile_segment_membership_seeds__flag_off__does_not_enqueue(
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True

    # When
    reconcile_segment_membership_seeds()

    # Then
    assert not Task.objects.filter(
        task_identifier=seed_organisation_identities.task_identifier,
        serialized_args=Task.serialize_data((project.organisation_id,)),
    ).exists()


def test_reconcile_segment_membership_seeds__already_seeded__does_not_enqueue(
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    SegmentMembershipSeed.objects.create(
        organisation=project.organisation, seeded_at=timezone.now()
    )

    # When
    reconcile_segment_membership_seeds()

    # Then
    assert not Task.objects.filter(
        task_identifier=seed_organisation_identities.task_identifier,
        serialized_args=Task.serialize_data((project.organisation_id,)),
    ).exists()


def test_reconcile_segment_membership_seeds__seed_already_pending__does_not_enqueue(
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a seed for the org is already in flight (a large org still loading)
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR
    seed_organisation_identities.delay(args=(project.organisation_id,))

    # When
    reconcile_segment_membership_seeds()

    # Then
    assert (
        Task.objects.filter(
            task_identifier=seed_organisation_identities.task_identifier,
            completed=False,
            serialized_args=Task.serialize_data((project.organisation_id,)),
        ).count()
        == 1
    )


def test_refresh_all_segment_counts__no_clickhouse_creds__skips(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = False
    enqueue = mocker.patch.object(tasks, "enqueue_membership_refresh")

    # When
    refresh_all_segment_counts()

    # Then
    enqueue.assert_not_called()


def test_refresh_all_segment_counts__no_live_segments__does_nothing(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
) -> None:
    # Given a project but no live segments, so there are no organisations to seed
    settings.CLICKHOUSE_ENABLED = True
    enqueue = mocker.patch.object(tasks, "enqueue_membership_refresh")

    # When
    refresh_all_segment_counts()

    # Then
    enqueue.assert_not_called()


def test_refresh_all_segment_counts__live_segment_projects__staggers_evenly_by_org(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
) -> None:
    # Given three live-segment projects across two organisations
    project_a2 = Project.objects.create(name="a2", organisation=project.organisation)
    Segment.objects.create(name="seg-a2", project=project_a2)
    org_b = Organisation.objects.create(name="org-b")
    project_b = Project.objects.create(name="b1", organisation=org_b)
    Segment.objects.create(name="seg-b", project=project_b)
    settings.CLICKHOUSE_ENABLED = True
    settings.SEGMENT_MEMBERSHIP_REFRESH_PROJECT_STAGGER_WINDOW_HOURS = 4
    enqueue = mocker.patch.object(tasks, "enqueue_membership_refresh")

    # When
    refresh_all_segment_counts()

    # Then one call per project, ordered by (organisation_id, id) so an
    # organisation's projects refresh contiguously
    called = [
        (call.args[0].id, call.kwargs["delay_until"]) for call in enqueue.call_args_list
    ]
    expected_order = sorted(
        (project, project_a2, project_b), key=lambda p: (p.organisation_id, p.id)
    )
    assert [pid for pid, _ in called] == [p.id for p in expected_order]
    # spread evenly across the window: spacing = window / (total + 1)
    spacing = timedelta(hours=4) / 4
    delays = [delay for _, delay in called]
    assert delays[1] - delays[0] == spacing
    assert delays[2] - delays[1] == spacing


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


def test_refresh_project_segment_counts__ff_disabled__skips_and_purges_stale_counts(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
    segment: Segment,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    spy = mocker.patch.object(tasks, "open_clickhouse_cursor")
    SegmentMembershipCount.objects.create(
        segment=segment,
        environment=environment,
        count=15,
        last_synced_at=timezone.now(),
    )

    # When
    refresh_project_segment_counts(project.id)

    # Then
    spy.assert_not_called()
    assert not SegmentMembershipCount.objects.filter(
        segment=segment, environment=environment
    ).exists()
    assert any(
        e["event"] == "refresh.project.skipped"
        and e["reason"] == "ff_disabled"
        and e["stale_counts__count"] == 1
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
    mocker.patch.object(tasks, "compute_segment_counts_for_project", return_value=[])

    # When
    refresh_project_segment_counts(project.id)

    # Then the stale row is gone -- pairs that no longer match drop out entirely
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

    # Then
    assert not SegmentMembershipCount.objects.filter(
        segment=segment, environment=environment
    ).exists()
