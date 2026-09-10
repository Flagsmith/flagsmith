from django.conf import settings
from django.views import View
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request

from organisations.invites.services import is_valid_registration_invite


class CurrentUser(IsAuthenticated):
    """
    Class to ensure that users of the platform can only retrieve details of themselves.
    """

    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        return view.action == "me"

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        return obj.id == request.user.id


class IsSignupAllowed(AllowAny):
    def has_permission(self, request: Request, view: View) -> bool:
        if not settings.PREVENT_SIGNUP:
            return True

        # Signups are otherwise prevented, but a valid invite should still
        # let someone through: `PREVENT_SIGNUP` is meant to stop self-serve
        # signup, not registration via an invite link or invited email.
        return is_valid_registration_invite(
            sign_up_type=request.data.get("sign_up_type"),
            email=request.data.get("email") or "",
            invite_hash=request.data.get("invite_hash"),
        )


class IsPasswordLoginAllowed(AllowAny):
    def has_permission(self, request: Request, view: View) -> bool:
        return not settings.PREVENT_EMAIL_PASSWORD
