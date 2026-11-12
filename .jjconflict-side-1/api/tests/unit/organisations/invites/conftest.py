import pytest

from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation
from users.models import FFAdminUser


@pytest.fixture()
def invite_link(organisation: Organisation) -> InviteLink:
    _invite_link: InviteLink = InviteLink.objects.create(organisation=organisation)
    return _invite_link


@pytest.fixture()
def invite(
    organisation: Organisation,
    admin_user: FFAdminUser,
    staff_user: FFAdminUser,
) -> Invite:
    _invite: Invite = Invite.objects.create(
        organisation=organisation, email=staff_user.email, invited_by=admin_user
    )
    return _invite
