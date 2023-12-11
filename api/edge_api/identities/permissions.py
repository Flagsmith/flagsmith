from contextlib import suppress

from django.http import HttpRequest
from django.views import View
from rest_framework.permissions import BasePermission

from environments.models import Environment
from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_IDENTITIES,
)


class EdgeIdentityWithIdentifierViewPermissions(BasePermission):
    def has_permission(self, request, view):
        environment_api_key = view.kwargs.get("environment_api_key")
        with suppress(Environment.DoesNotExist):
            environment = Environment.objects.get(api_key=environment_api_key)
            return request.user.has_environment_permission(
                UPDATE_FEATURE_STATE, environment
            )
        return False


class GetEdgeIdentityOverridesPermission(BasePermission):
    def has_permission(self, request: HttpRequest, view: View) -> bool:
        environment_api_key = view.kwargs.get("environment_api_key")
        with suppress(Environment.DoesNotExist):
            environment = Environment.objects.get(api_key=environment_api_key)
            return request.user.has_environment_permission(VIEW_IDENTITIES, environment)
        return False
