from django.contrib.admin.sites import AdminSite
from django.utils import timezone
from pytest_mock import MockerFixture
from segment_membership.admin import SegmentMembershipSeedAdmin

from organisations.models import Organisation
from segment_membership.models import SegmentMembershipSeed


def test_segment_membership_seed_admin_force_reseed__queryset__clears_marker(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given a previously seeded org
    seed = SegmentMembershipSeed.objects.create(
        organisation=organisation, seeded_at=timezone.now()
    )
    admin = SegmentMembershipSeedAdmin(SegmentMembershipSeed, AdminSite())

    # When support forces a re-seed from the admin
    admin.force_reseed(
        request=mocker.MagicMock(), queryset=SegmentMembershipSeed.objects.all()
    )

    # Then the marker is cleared so the next reconciler tick re-seeds the org
    seed.refresh_from_db()
    assert seed.seeded_at is None
