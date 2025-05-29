from django.conf import settings
from django.views import View
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request

from organisations.invites.models import Invite, InviteLink


class CurrentUser(IsAuthenticated):
    """
    Class to ensure that users of the platform can only retrieve details of themselves.
    """

    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        return view.action == "me"

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        return obj.id == request.user.id


class IsSignupAllowed(AllowAny):
    message = "Signing up without an invitation is disabled. Please contact your administrator."

    def has_permission(self, request: Request, view: View) -> bool:
        if not settings.PREVENT_SIGNUP:
            return True

        email = request.data.get("email")
        if email and Invite.objects.filter(email__iexact=email).exists():
            return True

        invite_hash = request.data.get("invite_hash")
        if invite_hash:
            try:
                invite_link = InviteLink.objects.get(hash=invite_hash)
            except InviteLink.DoesNotExist:
                pass

        if not invite_link.is_expired:
            return True

        raise PermissionDenied(self.message)


class IsPasswordLoginAllowed(AllowAny):
    def has_permission(self, request: Request, view: View) -> bool:
        return not settings.PREVENT_EMAIL_PASSWORD
