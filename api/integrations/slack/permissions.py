from rest_framework.permissions import BasePermission


class OauthInitPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.get_permitted_environments("VIEW_ENVIRONMENT")
            .filter(api_key=view.kwargs.get("environment_api_key"))
            .exists()
        )
