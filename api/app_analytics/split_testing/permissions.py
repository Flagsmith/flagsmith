from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet

from environments.models import Environment
from environments.permissions.constants import VIEW_ENVIRONMENT


class SplitTestPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: ModelViewSet) -> bool:
        if not super().has_permission(request, view):
            return False

        environment_id = request.query_params.get("environment_id")

        if not environment_id:
            return False

        environment = Environment.objects.get(id=environment_id)

        return request.user.has_environment_permission(
            permission=VIEW_ENVIRONMENT, environment=environment
        )
