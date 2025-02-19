import pytest

from organisations.invites.models import InviteLink
from organisations.models import Organisation


@pytest.fixture()
def invite_link(organisation: Organisation) -> InviteLink:
    return InviteLink.objects.create(organisation=organisation)  # type: ignore[no-any-return]
