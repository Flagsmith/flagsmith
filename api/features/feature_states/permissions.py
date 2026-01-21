from common.environments.permissions import UPDATE_FEATURE_STATE
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from environments.models import Environment


class EnvironmentUpdateFeatureStatePermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        environment_key = view.kwargs.get("environment_key")
        try:
            environment = Environment.objects.get(api_key=environment_key)
        except Environment.DoesNotExist:
            return False

        return request.user.has_environment_permission(  # type: ignore[union-attr,no-any-return]
            UPDATE_FEATURE_STATE, environment
        )
