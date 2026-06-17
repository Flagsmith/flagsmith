from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project
from segment_membership.services import (
    compute_segment_counts_for_project,
    get_projects_to_process,
    is_membership_enabled,
    open_clickhouse_cursor,
)
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


def test_open_clickhouse_cursor__no_log_comment__yields_cursor(
    mocker: MockerFixture,
) -> None:
    # Given
    cursor = MagicMock()
    connections = mocker.patch("segment_membership.services.connections")
    connections.__getitem__.return_value.cursor.return_value.__enter__.return_value = (
        cursor
    )

    # When
    with open_clickhouse_cursor() as opened:
        assert opened is cursor

    # Then
    cursor.cursor.set_settings.assert_not_called()


def test_open_clickhouse_cursor__with_log_comment__sets_session_attribution(
    mocker: MockerFixture,
) -> None:
    # Given
    cursor = MagicMock()
    connections = mocker.patch("segment_membership.services.connections")
    connections.__getitem__.return_value.cursor.return_value.__enter__.return_value = (
        cursor
    )

    # When
    with open_clickhouse_cursor(
        log_comment="flagsmith:segment_membership:refresh:org_1:project_2"
    ):
        pass

    # Then the comment lands as a clickhouse-driver session setting so every
    # query the cursor issues is attributable in CH's query_log.
    cursor.cursor.set_settings.assert_called_once_with(
        {"log_comment": "flagsmith:segment_membership:refresh:org_1:project_2"}
    )


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


def test_compute_segment_counts_for_project__one_segment__returns_membership_instances(
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
    cursor.fetchall.return_value = [(segment.id, environment.api_key, 7)]

    # When
    result = compute_segment_counts_for_project(project, cursor)

    # Then
    [membership] = result
    assert membership.segment_id == segment.id
    assert membership.environment_id == environment.id
    assert membership.count == 7
    assert membership.last_synced_at is None
    sql = cursor.execute.call_args.args[0]
    assert f"SELECT {segment.id} AS segment_id" in sql
    # FINAL forces ReplacingMergeTree dedup at read time.
    assert "FROM IDENTITIES AS i FINAL" in sql
    assert "GROUP BY i.environment_id" in sql


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
