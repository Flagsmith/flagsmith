import typing

import pytest
from django.db.utils import IntegrityError

from organisations.invites.exceptions import InviteLinksDisabledError
from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation

if typing.TYPE_CHECKING:
    from django.core.mail import EmailMessage
    from pytest_django.fixtures import SettingsWrapper


def test_cannot_create_invite_link_if_disabled(settings: "SettingsWrapper") -> None:
    # Given
    settings.DISABLE_INVITE_LINKS = True

    # When & Then
    with pytest.raises(InviteLinksDisabledError):
        InviteLink.objects.create()


@pytest.mark.django_db
def test_save_invalid_invite__dont_send(mailoutbox: "list[EmailMessage]") -> None:
    # Given
    email = "unknown@test.com"
    organisation = Organisation.objects.create(name="ssg")
    invite = Invite(email=email, organisation=organisation)
    invite.save()
    invalid_invite = Invite(email=email, organisation=organisation)

    # When
    with pytest.raises(IntegrityError):
        invalid_invite.save()

    # Then
    assert len(mailoutbox) == 1
