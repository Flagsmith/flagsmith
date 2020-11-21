from rest_framework.permissions import IsAuthenticated


class CurrentUser(IsAuthenticated):
    """
    Class to ensure that users of the platform can only retrieve details of themselves.
    """

    def has_permission(self, request, view):
        return view.action == "me"

    def has_object_permission(self, request, view, obj):
        return obj.id == request.user.id
