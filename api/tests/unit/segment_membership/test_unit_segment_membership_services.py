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
    # Given the FoF flag is not enabled (default state of the test
    # OpenFeature provider)
    # When the helper resolves the flag for the organisation
    # Then it returns False
    assert is_membership_enabled(organisation) is False


def test_is_membership_enabled__flag_on__returns_true(
    organisation: Organisation,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given the FoF flag is enabled
    enable_features("segment_membership_inspection")

    # When the helper resolves the flag
    # Then it returns True
    assert is_membership_enabled(organisation) is True


def test_open_clickhouse_cursor__no_log_comment__yields_cursor(
    mocker: MockerFixture,
) -> None:
    # Given the `clickhouse` connection alias yields a mocked cursor
    cursor = MagicMock()
    connections = mocker.patch("segment_membership.services.connections")
    connections.__getitem__.return_value.cursor.return_value.__enter__.return_value = (
        cursor
    )

    # When the context manager is entered without a log_comment
    with open_clickhouse_cursor() as opened:
        assert opened is cursor

    # Then no session settings are applied (log_comment not set)
    cursor.cursor.set_settings.assert_not_called()


def test_open_clickhouse_cursor__with_log_comment__sets_session_attribution(
    mocker: MockerFixture,
) -> None:
    # Given the `clickhouse` connection alias yields a mocked cursor
    cursor = MagicMock()
    connections = mocker.patch("segment_membership.services.connections")
    connections.__getitem__.return_value.cursor.return_value.__enter__.return_value = (
        cursor
    )

    # When the context manager opens with a log_comment
    with open_clickhouse_cursor(
        log_comment="flagsmith:segment_membership:refresh:org_1:project_2"
    ):
        pass

    # Then the comment lands as a clickhouse-driver session setting so
    # every query the cursor issues is attributable in CH's query_log.
    cursor.cursor.set_settings.assert_called_once_with(
        {"log_comment": "flagsmith:segment_membership:refresh:org_1:project_2"}
    )


def test_get_projects_to_process__no_canonical_segments__yields_nothing(
    project: Project,
) -> None:
    # Given a project with no canonical segments
    # When iterating projects to process
    # Then nothing is yielded
    assert list(get_projects_to_process()) == []


def test_get_projects_to_process__ff_disabled__skips_organisation(
    project: Project,
    segment: Segment,
) -> None:
    # Given a project with a canonical segment but FoF flag off
    # When iterating projects to process
    # Then the project is skipped
    assert list(get_projects_to_process()) == []


def test_get_projects_to_process__ff_enabled__yields_project(
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a project with a canonical segment and the FoF flag on
    enable_features("segment_membership_inspection")

    # When iterating projects to process
    # Then the project is yielded
    assert list(get_projects_to_process()) == [project]


def test_get_projects_to_process__multiple_segments_per_project__yields_project_once(
    project: Project,
    segment: Segment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a project with multiple canonical segments
    enable_features("segment_membership_inspection")
    Segment.objects.create(name="another", project=project)

    # When iterating projects to process
    # Then the project is yielded once, not once per segment
    assert list(get_projects_to_process()) == [project]


def test_compute_segment_counts_for_project__no_segments__returns_empty(
    project: Project,
) -> None:
    # Given a project with no canonical segments
    cursor = MagicMock()

    # When counts are computed
    result = compute_segment_counts_for_project(project, cursor)

    # Then the result is empty and ClickHouse was not queried
    assert result == []
    cursor.execute.assert_not_called()


def test_compute_segment_counts_for_project__no_environments__returns_empty(
    project: Project,
    segment: Segment,
) -> None:
    # Given a project with a segment but no environments
    project.environments.all().delete()
    cursor = MagicMock()

    # When counts are computed
    result = compute_segment_counts_for_project(project, cursor)

    # Then the result is empty and ClickHouse was not queried
    assert result == []
    cursor.execute.assert_not_called()


def test_compute_segment_counts_for_project__one_segment__returns_membership_instances(
    project: Project,
    environment: Environment,
    segment: Segment,
    segment_rule: SegmentRule,
    mocker: MockerFixture,
) -> None:
    # Given a project with one segment, one environment, and a stubbed
    # SQL translator that emits a trivial predicate
    mocker.patch(
        "segment_membership.services.translate_segment",
        return_value="TRUE",
    )
    cursor = MagicMock()
    cursor.fetchall.return_value = [(segment.id, environment.api_key, 7)]

    # When counts are computed
    result = compute_segment_counts_for_project(project, cursor)

    # Then the row decodes into an unsaved SegmentMembershipCount keyed by
    # (segment, environment); last_synced_at left for the caller.
    assert len(result) == 1
    [membership] = result
    assert membership.segment_id == segment.id
    assert membership.environment_id == environment.id
    assert membership.count == 7
    assert membership.last_synced_at is None
    cursor.execute.assert_called_once()
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
    # Given a ClickHouse row whose env_key isn't in this project — would
    # only happen via stale/cross-project data, but we defend against it
    mocker.patch(
        "segment_membership.services.translate_segment",
        return_value="TRUE",
    )
    cursor = MagicMock()
    cursor.fetchall.return_value = [(segment.id, "ghost-env", 99)]

    # When counts are computed
    result = compute_segment_counts_for_project(project, cursor)

    # Then the unknown-env row is skipped, no spurious membership emitted
    assert result == []


def test_compute_segment_counts_for_project__untranslatable_segment__skips(
    project: Project,
    environment: Environment,
    segment: Segment,
    segment_rule: SegmentRule,
    mocker: MockerFixture,
) -> None:
    # Given a project with a segment whose predicate the translator can't compile
    mocker.patch(
        "segment_membership.services.translate_segment",
        return_value=None,
    )
    cursor = MagicMock()

    # When counts are computed
    result = compute_segment_counts_for_project(project, cursor)

    # Then the segment is skipped entirely (no row, not even count = 0)
    # and ClickHouse is not queried at all
    assert result == []
    cursor.execute.assert_not_called()
