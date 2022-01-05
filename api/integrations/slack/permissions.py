from rest_framework.permissions import BasePermission

from environments.models import Environment


class OauthInitPermission(BasePermission):
    def has_permission(self, request, view):
        environment = Environment.objects.get(
            api_key=view.kwargs.get("environment_api_key")
        )
        return request.user.is_environment_admin(environment)
