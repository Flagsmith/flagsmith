from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from environments.models import Environment


class FlagBisectPermission(BasePermission):
    """Environment admins only: the gates change what an environment serves."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not settings.FLAG_BISECT_ENABLED:
            return False
        environment = Environment.objects.filter(
            api_key=view.kwargs.get("environment_api_key")
        ).first()
        if environment is None:
            return False
        return bool(request.user.is_environment_admin(environment))  # type: ignore[union-attr]
