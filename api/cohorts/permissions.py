from common.environments.permissions import VIEW_ENVIRONMENT
from common.projects.permissions import MANAGE_SEGMENTS
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from environments.models import Environment
from users.models import FFAdminUser

_READ_ACTIONS = ("list", "retrieve")


class CohortPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        try:
            environment = Environment.objects.get(
                api_key=view.kwargs.get("environment_api_key")
            )
        except Environment.DoesNotExist:
            return False
        user: FFAdminUser = request.user  # type: ignore[assignment]
        if getattr(view, "action", None) in _READ_ACTIONS:
            return user.has_environment_permission(VIEW_ENVIRONMENT, environment)
        return user.has_project_permission(MANAGE_SEGMENTS, environment.project)
