from contextlib import suppress

from rest_framework.permissions import BasePermission

from environments.models import Environment
from environments.permissions.constants import UPDATE_FEATURE_STATE


class EdgeIdentityWithIdentifierViewPermissions(BasePermission):
    def has_permission(self, request, view):
        environment_api_key = view.kwargs.get("environment_api_key")
        with suppress(Environment.DoesNotExist):
            environment = Environment.objects.get(api_key=environment_api_key)
            return request.user.has_environment_permission(
                UPDATE_FEATURE_STATE, environment
            )
        return False
