from datetime import datetime
from unittest.mock import MagicMock

import pytest
from common.test_tools import RunTasksFixture
from django.db import connections
from flag_engine.segments.constants import EQUAL
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project
from segment_membership.services import (
    compute_segment_counts_for_project,
    enqueue_membership_refresh,
    get_projects_to_process,
    get_segment_members_page,
    is_membership_enabled,
)
from segment_membership.tasks import refresh_project_segment_counts
from segment_membership.types import SegmentMember
from segments.models import Condition, Segment, SegmentRule
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


def test_get_segment_members_page__untranslatable_segment__returns_empty_without_querying(
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
    open_cursor = mocker.patch("segment_membership.services.open_clickhouse_cursor")

    # When
    result = get_segment_members_page(segment, environment, cursor=None, limit=100)

    # Then
    assert result == []
    open_cursor.assert_not_called()


@pytest.fixture
def matching_segment(segment: Segment) -> Segment:
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, property="foo", operator=EQUAL, value="bar")
    return segment


@pytest.mark.clickhouse
def test_get_segment_members_page__deleted_identity__excluded(
    segment_membership_identities: None,
    matching_segment: Segment,
    environment: Environment,
    environment_api_key_str: str,
) -> None:
    # Given
    with connections["clickhouse"].cursor() as cursor:
        cursor.executemany(
            "INSERT INTO IDENTITIES "
            "(environment_id, identifier, identity_key, traits, is_deleted) VALUES",
            [(environment_api_key_str, "aaron", "aaron_key", {"foo": "bar"}, True)],  # type: ignore[list-item]
        )

    # When
    members = get_segment_members_page(
        matching_segment, environment, cursor=None, limit=100
    )

    # Then
    assert [member["identifier"] for member in members] == ["alice", "bob"]


@pytest.mark.clickhouse
def test_get_segment_members_page__duplicate_versions__returns_latest_once(
    segment_membership_identities: None,
    matching_segment: Segment,
    environment: Environment,
    environment_api_key_str: str,
) -> None:
    # Given
    # a newer version of alice that still matches the segment
    with connections["clickhouse"].cursor() as cursor:
        cursor.executemany(
            "INSERT INTO IDENTITIES "
            "(environment_id, identifier, identity_key, traits, inserted_at) VALUES",
            [
                (  # type: ignore[list-item]
                    environment_api_key_str,
                    "alice",
                    "alice_key",
                    {"foo": "bar", "version": "new"},
                    datetime(2099, 1, 1),
                )
            ],
        )

    # When
    members = get_segment_members_page(
        matching_segment, environment, cursor=None, limit=100
    )

    # Then
    # alice appears once, with the latest version's traits
    assert members == [
        SegmentMember(
            identifier="alice",
            identity_key="alice_key",
            traits={"foo": "bar", "version": "new"},
        ),
        SegmentMember(identifier="bob", identity_key="bob_key", traits={"foo": "bar"}),
    ]


@pytest.mark.clickhouse
def test_compute_segment_counts_for_project__deleted_identity__excluded_from_count(
    segment_membership_identities: None,
    matching_segment: Segment,
    project: Project,
    environment_api_key_str: str,
) -> None:
    # Given
    with connections["clickhouse"].cursor() as cursor:
        cursor.executemany(
            "INSERT INTO IDENTITIES "
            "(environment_id, identifier, identity_key, traits, is_deleted) VALUES",
            [(environment_api_key_str, "aaron", "aaron_key", {"foo": "bar"}, True)],  # type: ignore[list-item]
        )

    # When
    with connections["clickhouse"].cursor() as cursor:
        counts = compute_segment_counts_for_project(project, cursor)

    # Then
    assert len(counts) == 1
    assert counts[0].segment_id == matching_segment.id
    assert counts[0].count == 2


@pytest.mark.clickhouse
def test_get_segment_members_page__matching_identities__returns_members_ordered_by_identifier(
    segment_membership_identities: None,
    matching_segment: Segment,
    environment: Environment,
) -> None:
    # Given / When
    members = get_segment_members_page(
        matching_segment, environment, cursor=None, limit=100
    )

    # Then
    assert members == [
        SegmentMember(
            identifier="alice",
            identity_key="alice_key",
            traits={"foo": "bar"},
        ),
        SegmentMember(
            identifier="bob",
            identity_key="bob_key",
            traits={"foo": "bar"},
        ),
    ]


@pytest.mark.clickhouse
def test_get_segment_members_page__cursor__returns_rows_after_cursor(
    segment_membership_identities: None,
    matching_segment: Segment,
    environment: Environment,
) -> None:
    # Given / When
    members = get_segment_members_page(
        matching_segment, environment, cursor="alice", limit=100
    )

    # Then
    assert members == [
        SegmentMember(
            identifier="bob",
            identity_key="bob_key",
            traits={"foo": "bar"},
        ),
    ]


@pytest.mark.clickhouse
def test_get_segment_members_page__limit__caps_results(
    segment_membership_identities: None,
    matching_segment: Segment,
    environment: Environment,
) -> None:
    # Given / When
    members = get_segment_members_page(
        matching_segment, environment, cursor=None, limit=1
    )

    # Then
    assert members == [
        SegmentMember(
            identifier="alice",
            identity_key="alice_key",
            traits={"foo": "bar"},
        ),
    ]


@pytest.mark.parametrize(
    "q,expected_result",
    [
        pytest.param(
            "ali",
            [
                SegmentMember(
                    identifier="alice",
                    identity_key="alice_key",
                    traits={"foo": "bar"},
                ),
            ],
            id="substring",
        ),
        pytest.param(
            "ALICE",
            [
                SegmentMember(
                    identifier="alice",
                    identity_key="alice_key",
                    traits={"foo": "bar"},
                ),
            ],
            id="case-insensitive",
        ),
        pytest.param("zzz", [], id="no-match"),
    ],
)
@pytest.mark.clickhouse
def test_get_segment_members_page__q__returns_expected(
    segment_membership_identities: None,
    matching_segment: Segment,
    environment: Environment,
    q: str,
    expected_result: list[SegmentMember],
) -> None:
    # Given / When
    members = get_segment_members_page(
        matching_segment,
        environment,
        cursor=None,
        limit=100,
        q=q,
    )

    # Then
    assert members == expected_result


@pytest.mark.clickhouse
def test_get_segment_members_page__q_matches_beyond_first_page__still_found(
    segment_membership_identities: None,
    matching_segment: Segment,
    environment: Environment,
) -> None:
    # Given / When
    members = get_segment_members_page(
        matching_segment,
        environment,
        cursor=None,
        limit=1,
        q="bob",
    )

    # Then
    assert members == [
        SegmentMember(
            identifier="bob",
            identity_key="bob_key",
            traits={"foo": "bar"},
        ),
    ]


def test_enqueue_membership_refresh__flag_on__enqueues_refresh(
    run_tasks: RunTasksFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
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
    compute_segment_counts_for_project_mock.assert_called_once_with(project, mocker.ANY)


def test_enqueue_membership_refresh__flag_off__does_not_enqueue(
    run_tasks: RunTasksFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
) -> None:
    # Given
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
    compute_segment_counts_for_project_mock.assert_not_called()


def test_enqueue_membership_refresh__refresh_already_pending__debounces(
    run_tasks: RunTasksFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
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
    assert compute_segment_counts_for_project_mock.call_count == 2
    compute_segment_counts_for_project_mock.assert_has_calls(
        [mocker.call(project, mocker.ANY), mocker.call(project_b, mocker.ANY)],
        any_order=True,
    )
