from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from environments.models import Environment
from users.models import FFAdminUser


class ExperimentationPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not settings.EXPERIMENTATION_ENABLED:
            return False

        try:
            environment = Environment.objects.get(
                api_key=view.kwargs.get("environment_api_key")
            )
        except Environment.DoesNotExist:
            return False

        user: FFAdminUser = request.user  # type: ignore[assignment]
        return user.is_environment_admin(environment)
