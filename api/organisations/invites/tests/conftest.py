import pytest

from organisations.invites.models import Invite, InviteLink


@pytest.fixture()
def invite_link(organisation):
    return InviteLink.objects.create(organisation=organisation)


@pytest.fixture()
def invite(organisation, admin_user):
    return Invite.objects.create(
        organisation=organisation, email="test@user.com", invited_by=admin_user
    )
