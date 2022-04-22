from rest_framework.permissions import IsAuthenticated

from environments.models import Environment
from environments.permissions.constants import VIEW_ENVIRONMENT


class EnvironmentIdentityTraitsPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        environment = Environment.objects.get(
            api_key=view.kwargs.get("environment_api_key")
        )
        return request.user.has_environment_permission(VIEW_ENVIRONMENT, environment)
