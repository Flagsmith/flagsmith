from unittest.mock import MagicMock

from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project
from segment_membership import services
from segment_membership.services import (
    compute_segment_counts_for_project,
    get_projects_to_process,
    is_membership_enabled,
    is_snowflake_configured,
    open_snowflake_session,
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


def test_is_snowflake_configured__all_set__returns_true(
    settings: SettingsWrapper,
) -> None:
    # Given every required SNOWFLAKE_* setting is populated
    settings.SNOWFLAKE_ACCOUNT = "acc"
    settings.SNOWFLAKE_USER = "u"
    settings.SNOWFLAKE_PRIVATE_KEY_PATH = "/key"
    settings.SNOWFLAKE_DATABASE = "db"
    settings.SNOWFLAKE_SCHEMA = "sch"
    settings.SNOWFLAKE_WAREHOUSE = "wh"

    # When checked
    # Then the helper reports the feature configured
    assert is_snowflake_configured() is True


def test_is_snowflake_configured__missing_account__returns_false(
    settings: SettingsWrapper,
) -> None:
    # Given one required setting is unset
    settings.SNOWFLAKE_ACCOUNT = None
    settings.SNOWFLAKE_USER = "u"
    settings.SNOWFLAKE_PRIVATE_KEY_PATH = "/key"
    settings.SNOWFLAKE_DATABASE = "db"
    settings.SNOWFLAKE_SCHEMA = "sch"
    settings.SNOWFLAKE_WAREHOUSE = "wh"

    # When checked
    # Then the helper reports the feature unconfigured
    assert is_snowflake_configured() is False


def test_open_snowflake_session__configured__yields_session_and_closes(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given populated SNOWFLAKE_* settings and a mocked Snowpark builder
    settings.SNOWFLAKE_ACCOUNT = "acc"
    settings.SNOWFLAKE_USER = "u"
    settings.SNOWFLAKE_ROLE = "ACCOUNTADMIN"
    settings.SNOWFLAKE_WAREHOUSE = "wh"
    settings.SNOWFLAKE_DATABASE = "db"
    settings.SNOWFLAKE_SCHEMA = "sch"
    settings.SNOWFLAKE_PRIVATE_KEY_PATH = "/key"

    fake_session = MagicMock()
    builder = MagicMock()
    builder.configs.return_value.create.return_value = fake_session
    mocker.patch.object(services, "Session", MagicMock(builder=builder))

    # When the context manager is entered and exited
    with open_snowflake_session() as sess:
        # Then it yields the underlying Snowpark session...
        assert sess is fake_session

    # ...and closes it on exit
    fake_session.close.assert_called_once_with()


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


def test_compute_segment_counts_for_project__no_segments__returns_empty(
    project: Project,
) -> None:
    # Given a project with no canonical segments
    sess = MagicMock()

    # When counts are computed
    result = compute_segment_counts_for_project(project, sess)

    # Then the result is empty and Snowflake was not queried
    assert result == []
    sess.sql.assert_not_called()


def test_compute_segment_counts_for_project__no_environments__returns_empty(
    project: Project,
    segment: Segment,
) -> None:
    # Given a project with a segment but no environments
    project.environments.all().delete()
    sess = MagicMock()

    # When counts are computed
    result = compute_segment_counts_for_project(project, sess)

    # Then the result is empty and Snowflake was not queried
    assert result == []
    sess.sql.assert_not_called()


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
    sess = MagicMock()
    sess.sql.return_value.collect.return_value = [
        {"SEGMENT_ID": segment.id, "ENV_KEY": environment.api_key, "C": 7}
    ]

    # When counts are computed
    result = compute_segment_counts_for_project(project, sess)

    # Then Snowflake was queried once, the predicate landed in the SQL,
    # and the row decodes into an unsaved SegmentMembership keyed by
    # (segment, environment) — last_synced_at left for the caller
    assert len(result) == 1
    [membership] = result
    assert membership.segment_id == segment.id
    assert membership.environment_id == environment.id
    assert membership.count == 7
    assert membership.last_synced_at is None
    sess.sql.assert_called_once()
    sql = sess.sql.call_args.args[0]
    assert f"SELECT {segment.id} AS segment_id" in sql
    assert "GROUP BY i.environment_id" in sql


def test_compute_segment_counts_for_project__unknown_env_key_in_row__skips(
    project: Project,
    environment: Environment,
    segment: Segment,
    segment_rule: SegmentRule,
    mocker: MockerFixture,
) -> None:
    # Given a Snowflake row whose env_key isn't in this project — would
    # only happen via stale/cross-project data, but we defend against it
    mocker.patch(
        "segment_membership.services.translate_segment",
        return_value="TRUE",
    )
    sess = MagicMock()
    sess.sql.return_value.collect.return_value = [
        {"SEGMENT_ID": segment.id, "ENV_KEY": "ghost-env", "C": 99}
    ]

    # When counts are computed
    result = compute_segment_counts_for_project(project, sess)

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
    sess = MagicMock()

    # When counts are computed
    result = compute_segment_counts_for_project(project, sess)

    # Then the segment is skipped entirely (no row, not even count = 0)
    # and Snowflake is not queried at all
    assert result == []
    sess.sql.assert_not_called()
