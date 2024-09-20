from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated


class CurrentUser(IsAuthenticated):
    """
    Class to ensure that users of the platform can only retrieve details of themselves.
    """

    def has_permission(self, request, view):
        return view.action == "me"

    def has_object_permission(self, request, view, obj):
        return obj.id == request.user.id


class IsSignupAllowed(AllowAny):
    def has_permission(self, request, view):
        return not settings.PREVENT_SIGNUP
