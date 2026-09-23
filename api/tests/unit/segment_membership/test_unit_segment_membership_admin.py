from django.contrib.admin.sites import AdminSite
from django.utils import timezone
from pytest_mock import MockerFixture

from organisations.models import Organisation
from segment_membership.admin import SegmentMembershipSeedAdmin
from segment_membership.models import SegmentMembershipSeed


def test_segment_membership_seed_admin_force_reseed__queryset__clears_marker_and_enqueues_seed(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    seed = SegmentMembershipSeed.objects.create(
        organisation=organisation, seeded_at=timezone.now()
    )
    seed_task = mocker.patch("segment_membership.tasks.seed_organisation_identities")
    admin = SegmentMembershipSeedAdmin(SegmentMembershipSeed, AdminSite())

    # When
    admin.force_reseed(
        request=mocker.MagicMock(), queryset=SegmentMembershipSeed.objects.all()
    )

    # Then
    seed.refresh_from_db()
    assert seed.seeded_at is None
    seed_task.delay.assert_called_once_with(args=(organisation.id,))
