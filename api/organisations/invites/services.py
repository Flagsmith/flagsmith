from users.models import SignUpType

from .models import Invite, InviteLink


def is_valid_registration_invite(
    *, sign_up_type: str | None, email: str, invite_hash: str | None
) -> bool:
    match sign_up_type:
        case SignUpType.INVITE_LINK.value:
            invite_link = InviteLink.objects.filter(hash=invite_hash).first()
            return invite_link is not None and not invite_link.is_expired
        case SignUpType.INVITE_EMAIL.value:
            return Invite.objects.filter(email__iexact=email.lower()).exists()
        case _:
            return False
