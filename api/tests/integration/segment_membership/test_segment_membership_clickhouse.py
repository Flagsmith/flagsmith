import uuid

import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from projects.models import Project
from segment_membership.models import SegmentMembershipCount
from segment_membership.services import (
    compute_segment_counts_for_project,
    open_clickhouse_cursor,
)
from segment_membership.tasks import (
    backfill_identities_to_clickhouse,
    refresh_project_segment_counts,
)
from tests.types import EnableFeaturesFixture


@pytest.mark.clickhouse
def test_compute_segment_counts_for_project__matching_identities__counts_real_rows(
    segment_membership_identities: None,
    project: int,
    environment: int,
    segment: int,
) -> None:
    # Given the `segment` fixture (matches `foo=bar`) and the seeded identities

    # When
    with open_clickhouse_cursor() as cursor:
        result = compute_segment_counts_for_project(
            Project.objects.get(pk=project), cursor
        )

    # Then only the two matching identities are counted, for the right env
    [membership] = result
    assert membership.segment_id == segment
    assert membership.environment_id == environment
    assert membership.count == 2


@pytest.mark.clickhouse
def test_refresh_project_segment_counts__matching_identities__upserts_real_counts(
    segment_membership_identities: None,
    settings: SettingsWrapper,
    project: int,
    environment: int,
    segment: int,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given the org has segment-membership inspection on and ClickHouse enabled
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True

    # When the refresh task runs end-to-end against real ClickHouse
    refresh_project_segment_counts(project)

    # Then the (segment, environment) count row reflects the two matches
    membership = SegmentMembershipCount.objects.get(
        segment_id=segment, environment_id=environment
    )
    assert membership.count == 2
    assert membership.last_synced_at is not None


@pytest.mark.clickhouse
def test_backfill_identities_to_clickhouse__happy_path__rows_land_in_clickhouse(
    clickhouse_db: None,
    settings: SettingsWrapper,
    mocker: MockerFixture,
    project: int,
    environment: int,
    environment_api_key: str,
    segment: int,
    enable_features: EnableFeaturesFixture,
    log: StructuredLogCapture,
) -> None:
    # Given segment-membership inspection is on, ClickHouse is enabled, and
    # Dynamo yields two identities for the environment
    enable_features("segment_membership_inspection")
    settings.CLICKHOUSE_ENABLED = True
    refresh_dispatch = mocker.patch(
        "segment_membership.tasks.refresh_project_segment_counts"
    )
    wrapper = mocker.MagicMock(is_enabled=True)
    wrapper.iter_all_items_paginated.return_value = iter(
        [
            {
                "identity_uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "identifier": "a",
                "composite_key": "k1",
                "environment_api_key": environment_api_key,
                "created_date": "2026-05-08T00:00:00Z",
                "identity_traits": [{"trait_key": "foo", "trait_value": "bar"}],
            },
            {
                "identity_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "identifier": "b",
                "composite_key": "k2",
                "environment_api_key": environment_api_key,
                "created_date": "2026-05-08T00:00:00Z",
                "identity_traits": [],
            },
        ]
    )
    mocker.patch("segment_membership.tasks.DynamoIdentityWrapper", return_value=wrapper)

    # When the backfill task runs end-to-end against real ClickHouse
    backfill_identities_to_clickhouse()

    # Then both identities actually land in IDENTITIES, keyed by env api key
    with open_clickhouse_cursor() as cursor:
        cursor.execute(
            "SELECT identifier, identity_key FROM IDENTITIES FINAL "
            "WHERE environment_id = %(env)s ORDER BY identifier",
            {"env": environment_api_key},
        )
        rows = cursor.fetchall()
    assert [(row[0], row[1]) for row in rows] == [("a", "k1"), ("b", "k2")]
    # and the project's count refresh is dispatched
    refresh_dispatch.delay.assert_called_once_with(args=(project,))
    assert any(
        e["event"] == "backfill.environment.completed" and e["rows__count"] == 2
        for e in log.events
    )


@pytest.mark.clickhouse
def test_open_clickhouse_cursor__with_log_comment__lands_in_query_log(
    clickhouse_db: None,
) -> None:
    # Given a unique log_comment
    log_comment = f"flagsmith:test:{uuid.uuid4()}"

    # When a query runs on a cursor opened with that log_comment
    with open_clickhouse_cursor(log_comment=log_comment) as cursor:
        cursor.execute("SELECT 1")

    # Then the query is attributable in CH's query_log by that comment. The
    # query_log flushes asynchronously, so flush before reading.
    with open_clickhouse_cursor() as cursor:
        cursor.execute("SYSTEM FLUSH LOGS")
        cursor.execute(
            "SELECT count() FROM system.query_log WHERE log_comment = %(lc)s",
            {"lc": log_comment},
        )
        [(count,)] = cursor.fetchall()
    assert count >= 1
