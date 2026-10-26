from io import StringIO
from unittest.mock import MagicMock

from django.core.management import call_command
from mypy_boto3_dynamodb.service_resource import Table
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from projects.models import Project
from segment_membership.models import SegmentMembershipSeed
from segments.models import Segment

COMMAND = "seed_segment_membership"


def test_seed_segment_membership__organisation_id__runs_the_seed_inline(
    mocker: MockerFixture,
    project: Project,
) -> None:
    # Given
    seed = mocker.patch(
        "segment_membership.management.commands."
        "seed_segment_membership.seed_organisation_identities"
    )

    # When
    call_command(COMMAND, project.organisation_id, stdout=StringIO())

    # Then the task runs in this process rather than being queued, so no
    # task timeout applies and nothing retries it
    seed.assert_called_once_with(project.organisation_id, ignore_feature_flag=False)
    seed.delay.assert_not_called()


def test_seed_segment_membership__ignore_feature_flag__seeds_with_flag_off(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    project: Project,
    segment: Segment,
    flagsmith_identities_table: Table,
) -> None:
    # Given the organisation has not been let into the beta yet
    settings.CLICKHOUSE_ENABLED = True
    cursor = MagicMock()
    open_cursor = mocker.patch("segment_membership.tasks.open_clickhouse_cursor")
    open_cursor.return_value.__enter__.return_value = cursor
    mocker.patch("segment_membership.tasks.enqueue_membership_refresh")

    # When
    call_command(
        COMMAND,
        project.organisation_id,
        "--ignore-feature-flag",
        stdout=StringIO(),
    )

    # Then the seed runs to completion regardless
    assert SegmentMembershipSeed.objects.filter(
        organisation=project.organisation, seeded_at__isnull=False
    ).exists()
