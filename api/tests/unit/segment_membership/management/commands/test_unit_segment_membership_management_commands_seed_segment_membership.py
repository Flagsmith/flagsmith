from django.core.management import call_command
from pytest_mock import MockerFixture

from organisations.models import Organisation


def test_seed_segment_membership__org_id__enqueues_seed_for_org(
    mocker: MockerFixture,
    organisation: Organisation,
) -> None:
    # Given support wants to seed one org on demand (e.g. after a failed seed)
    seed = mocker.patch(
        "segment_membership.management.commands.seed_segment_membership"
        ".seed_organisation_identities"
    )

    # When
    call_command("seed_segment_membership", organisation.id)

    # Then the seed is queued for that org alone, leaving every other org
    # untouched.
    seed.delay.assert_called_once_with(args=(organisation.id,))
