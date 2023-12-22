import pytest

from organisations.invites.models import Invite, InviteLink


@pytest.fixture()
def invite_link(organisation):
    return InviteLink.objects.create(organisation=organisation)


@pytest.fixture()
def invite(organisation, admin_user, test_user):
    return Invite.objects.create(
        organisation=organisation, email=test_user.email, invited_by=admin_user
    )
