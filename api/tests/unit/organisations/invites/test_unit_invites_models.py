import pytest

from organisations.invites.exceptions import InviteLinksDisabledError
from organisations.invites.models import InviteLink


def test_cannot_create_invite_link_if_disabled(settings):
    settings.DISABLE_INVITE_LINKS = True
    with pytest.raises(InviteLinksDisabledError):
        InviteLink.objects.create()
