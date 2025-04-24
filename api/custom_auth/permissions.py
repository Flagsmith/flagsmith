from django.conf import settings
from django.views import View
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request


class CurrentUser(IsAuthenticated):
    """
    Class to ensure that users of the platform can only retrieve details of themselves.
    """

    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        return super().has_permission(request, view) and view.action == "me"

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        return obj.id == request.user.id


class IsSignupAllowed(AllowAny):
    def has_permission(self, request: Request, view: View) -> bool:
        return not settings.PREVENT_SIGNUP


class IsPasswordLoginAllowed(AllowAny):
    def has_permission(self, request: Request, view: View) -> bool:
        return not settings.PREVENT_EMAIL_PASSWORD
