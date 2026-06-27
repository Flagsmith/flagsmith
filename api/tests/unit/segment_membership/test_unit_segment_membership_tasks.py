from unittest.mock import MagicMock

from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from task_processor.models import Task

from environments.models import Environment
from projects.models import Project
from segment_membership import tasks
from segment_membership.models import SegmentMembershipCount, SegmentMembershipSeed
from segment_membership.tasks import (
    reconcile_segment_membership_seeds,
    refresh_project_segment_counts,
    seed_organisation_identities,
)
from segments.models import Segment
from tests.types import EnableFeaturesFixture

UUID_A = "f47ac10b-58cc-4372-a567-0e02b2c3d479"


def _one_identity_doc(environment: Environment) -> dict[str, object]:
    return {
        "identity_uuid": UUID_A,
        "identifier": "a",
        "composite_key": "k1",
        "environment_api_key": environment.api_key,
        "created_date": "2026-05-08T00:00:00Z",
        "identity_traits": [],
    }


def _pending_seed_count(organisation_id: int) -> int:
    return Task.objects.filter(
        task_identifier=seed_organisation_identities.task_identifier,
        completed=False,
        serialized_args=Task.serialize_data((organisation_id,)),
    ).count()


# --- seed_organisation_identities ------------------------------------------


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
    assert any(e["event"] == "seed.skipped" for e in log.events)


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
    # Given the org was queued for a seed but its flag is now off -- the task
    # re-checks the flag defensively so a stale enqueue can't load data.
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
        [_one_identity_doc(environment)]
    )
    mocker.patch.object(tasks, "DynamoIdentityWrapper", return_value=wrapper)

    # When
    seed_organisation_identities(project.organisation_id)

    # Then
    assert any(e["event"] == "seed.environment.failed" for e in log.events)


def test_seed_organisation_identities__success__stamps_scan_start_inserted_at(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given the scan starts at a known instant
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    scan_start = timezone.now()
    mocker.patch("segment_membership.tasks.timezone.now", return_value=scan_start)
    cursor = MagicMock()
    open_cursor = mocker.patch.object(tasks, "open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    mocker.patch.object(tasks, "refresh_project_segment_counts")
    wrapper = MagicMock(is_enabled=True)
    wrapper.iter_all_items_paginated.return_value = iter(
        [_one_identity_doc(environment)]
    )
    mocker.patch.object(tasks, "DynamoIdentityWrapper", return_value=wrapper)

    # When
    seed_organisation_identities(project.organisation_id)

    # Then every inserted row is versioned at scan start, not insert time, so
    # any CDC write landing mid-scan (carrying a later timestamp) wins dedup.
    inserted_rows = cursor.executemany.call_args.args[1]
    assert inserted_rows
    assert all(row[-1] == scan_start for row in inserted_rows)


def test_seed_organisation_identities__success__marks_org_seeded(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    cursor = MagicMock()
    open_cursor = mocker.patch.object(tasks, "open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    mocker.patch.object(tasks, "refresh_project_segment_counts")
    wrapper = MagicMock(is_enabled=True)
    wrapper.iter_all_items_paginated.return_value = iter([])
    mocker.patch.object(tasks, "DynamoIdentityWrapper", return_value=wrapper)

    # When
    seed_organisation_identities(project.organisation_id)

    # Then the org carries a completed seed marker, so the reconciler never
    # seeds it again.
    assert SegmentMembershipSeed.objects.filter(
        organisation=project.organisation, seeded_at__isnull=False
    ).exists()


def test_seed_organisation_identities__success__fans_out_refresh_per_project(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given an org with two segment-bearing projects
    enable_features("segment_membership_inspection")
    project_b = Project.objects.create(
        name="project-b", organisation=project.organisation
    )
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
    seed_organisation_identities(project.organisation_id)

    # Then
    dispatched_ids = {
        call.kwargs["args"][0] for call in refresh_dispatch.delay.call_args_list
    }
    assert dispatched_ids == {project.id, project_b.id}


# --- reconcile_segment_membership_seeds ------------------------------------


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
    assert _pending_seed_count(project.organisation_id) == 0


def test_reconcile_segment_membership_seeds__flagged_unseeded_org__enqueues_seed(
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given an opted-in org with a live segment and no seed yet
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True

    # When
    reconcile_segment_membership_seeds()

    # Then exactly one seed is queued for the org
    assert _pending_seed_count(project.organisation_id) == 1


def test_reconcile_segment_membership_seeds__flag_off__does_not_enqueue(
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
) -> None:
    # Given a project with a live segment but the org is not opted in
    settings.CLICKHOUSE_ENABLED = True

    # When
    reconcile_segment_membership_seeds()

    # Then
    assert _pending_seed_count(project.organisation_id) == 0


def test_reconcile_segment_membership_seeds__already_seeded__does_not_enqueue(
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given the org was already seeded
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    SegmentMembershipSeed.objects.create(
        organisation=project.organisation, seeded_at=timezone.now()
    )

    # When
    reconcile_segment_membership_seeds()

    # Then no further seed is queued -- the org is loaded once, then CDC keeps
    # it fresh.
    assert _pending_seed_count(project.organisation_id) == 0


def test_reconcile_segment_membership_seeds__seed_already_pending__does_not_enqueue(
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a seed for the org is already in flight (a large org still loading)
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    seed_organisation_identities.delay(args=(project.organisation_id,))

    # When
    reconcile_segment_membership_seeds()

    # Then the tick does not pile on a second seed
    assert _pending_seed_count(project.organisation_id) == 1


# --- refresh_project_segment_counts (unchanged) ----------------------------


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
