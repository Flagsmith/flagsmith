from unittest.mock import MagicMock

from clickhouse_connect.driver import Client
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project
from segment_membership.services import (
    compute_segment_counts_for_project,
    get_projects_to_process,
    is_clickhouse_configured,
    is_membership_enabled,
    open_clickhouse_client,
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


def test_is_clickhouse_configured__host_set__returns_true(
    settings: SettingsWrapper,
) -> None:
    # Given CLICKHOUSE_HOST is populated and no DSN is set
    settings.CLICKHOUSE_URL = None
    settings.CLICKHOUSE_HOST = "ch.example.com"

    # When checked
    # Then the helper reports the feature configured
    assert is_clickhouse_configured() is True


def test_is_clickhouse_configured__url_set__returns_true(
    settings: SettingsWrapper,
) -> None:
    # Given CLICKHOUSE_URL is populated (DSN form) and HOST is unset
    settings.CLICKHOUSE_URL = "https://default:secret@ch.example.com:8443/default"
    settings.CLICKHOUSE_HOST = None

    # When checked
    # Then the helper reports the feature configured
    assert is_clickhouse_configured() is True


def test_is_clickhouse_configured__neither_set__returns_false(
    settings: SettingsWrapper,
) -> None:
    # Given neither URL nor HOST is set
    settings.CLICKHOUSE_URL = None
    settings.CLICKHOUSE_HOST = None

    # When checked
    # Then the helper reports the feature unconfigured
    assert is_clickhouse_configured() is False


def test_open_clickhouse_client__no_log_comment__yields_client_and_closes(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given no DSN set, populated discrete CLICKHOUSE_* settings, and a
    # mocked client factory
    settings.CLICKHOUSE_URL = None
    settings.CLICKHOUSE_HOST = "ch.example.com"
    settings.CLICKHOUSE_PORT = 8443
    settings.CLICKHOUSE_USER = "default"
    settings.CLICKHOUSE_PASSWORD = "secret"
    settings.CLICKHOUSE_DATABASE = "default"
    settings.CLICKHOUSE_SECURE = True

    fake_client = MagicMock(spec=Client)
    get_client = mocker.patch(
        "clickhouse_connect.get_client",
        return_value=fake_client,
    )

    # When the context manager is entered and exited
    with open_clickhouse_client() as client:
        # Then it yields the underlying clickhouse-connect client...
        assert client is fake_client

    # ...connects with the settings from `CLICKHOUSE_*` and the experimental
    # JSON-type flag flipped, with no log_comment override
    get_client.assert_called_once_with(
        host="ch.example.com",
        port=8443,
        username="default",
        password="secret",
        database="default",
        secure=True,
        settings={"allow_experimental_json_type": 1},
    )
    # ...and closes the client on exit
    fake_client.close.assert_called_once_with()


def test_open_clickhouse_client__url_set__hands_dsn_to_client(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given CLICKHOUSE_URL is set — clickhouse-connect's per-field args
    # take precedence over the DSN when both are passed, so the discrete
    # CLICKHOUSE_* settings must NOT leak through.
    settings.CLICKHOUSE_URL = "https://default:secret@ch.example.com:8443/segments?secure=true"
    settings.CLICKHOUSE_HOST = "should-not-be-used"
    settings.CLICKHOUSE_PORT = 9999
    settings.CLICKHOUSE_USER = "should-not-be-used"
    settings.CLICKHOUSE_PASSWORD = "should-not-be-used"
    settings.CLICKHOUSE_DATABASE = "should-not-be-used"
    settings.CLICKHOUSE_SECURE = False

    fake_client = MagicMock(spec=Client)
    get_client = mocker.patch(
        "clickhouse_connect.get_client",
        return_value=fake_client,
    )

    # When the context manager is entered
    with open_clickhouse_client():
        pass

    # Then the DSN is handed off exclusively
    get_client.assert_called_once_with(
        dsn="https://default:secret@ch.example.com:8443/segments?secure=true",
        settings={"allow_experimental_json_type": 1},
    )


def test_open_clickhouse_client__with_log_comment__sets_session_attribution(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given a log_comment passed through (the per-task attribution string)
    settings.CLICKHOUSE_URL = None
    settings.CLICKHOUSE_HOST = "ch.example.com"
    settings.CLICKHOUSE_PORT = 8443
    settings.CLICKHOUSE_USER = "default"
    settings.CLICKHOUSE_PASSWORD = ""
    settings.CLICKHOUSE_DATABASE = "default"
    settings.CLICKHOUSE_SECURE = True

    fake_client = MagicMock(spec=Client)
    get_client = mocker.patch(
        "clickhouse_connect.get_client",
        return_value=fake_client,
    )

    # When the context manager opens with a log_comment
    with open_clickhouse_client(
        log_comment="flagsmith:segment_membership:refresh:org_1:project_2"
    ):
        pass

    # Then the comment lands in the session-level `log_comment` setting so
    # every query the client issues is attributable in CH's query_log.
    _, kwargs = get_client.call_args
    assert kwargs["settings"] == {
        "allow_experimental_json_type": 1,
        "log_comment": "flagsmith:segment_membership:refresh:org_1:project_2",
    }


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
    client = MagicMock(spec=Client)

    # When counts are computed
    result = compute_segment_counts_for_project(project, client)

    # Then the result is empty and ClickHouse was not queried
    assert result == []
    client.query.assert_not_called()


def test_compute_segment_counts_for_project__no_environments__returns_empty(
    project: Project,
    segment: Segment,
) -> None:
    # Given a project with a segment but no environments
    project.environments.all().delete()
    client = MagicMock(spec=Client)

    # When counts are computed
    result = compute_segment_counts_for_project(project, client)

    # Then the result is empty and ClickHouse was not queried
    assert result == []
    client.query.assert_not_called()


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
    client = MagicMock(spec=Client)
    client.query.return_value.result_rows = [(segment.id, environment.api_key, 7)]

    # When counts are computed
    result = compute_segment_counts_for_project(project, client)

    # Then ClickHouse was queried once, the predicate landed in the SQL,
    # and the row decodes into an unsaved SegmentMembership keyed by
    # (segment, environment) — last_synced_at left for the caller
    assert len(result) == 1
    [membership] = result
    assert membership.segment_id == segment.id
    assert membership.environment_id == environment.id
    assert membership.count == 7
    assert membership.last_synced_at is None
    client.query.assert_called_once()
    sql = client.query.call_args.args[0]
    assert f"SELECT {segment.id} AS segment_id" in sql
    # The PoC's refresh query forces ReplacingMergeTree dedup at read
    # time — without FINAL the most-recent backfill might not be visible
    # until a merge pass runs.
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
    client = MagicMock(spec=Client)
    client.query.return_value.result_rows = [(segment.id, "ghost-env", 99)]

    # When counts are computed
    result = compute_segment_counts_for_project(project, client)

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
    client = MagicMock(spec=Client)

    # When counts are computed
    result = compute_segment_counts_for_project(project, client)

    # Then the segment is skipped entirely (no row, not even count = 0)
    # and ClickHouse is not queried at all
    assert result == []
    client.query.assert_not_called()
