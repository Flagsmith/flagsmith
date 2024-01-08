from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet

from environments.models import Environment
from environments.permissions.constants import VIEW_ENVIRONMENT

from .serializers import SplitTestQuerySerializer


class SplitTestPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: ModelViewSet) -> bool:
        if not super().has_permission(request, view):
            return False

        query_serializer = SplitTestQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        environment = Environment.objects.filter(
            id=query_serializer.validated_data["environment_id"]
        ).first()

        if environment is None:
            return False

        return request.user.has_environment_permission(
            permission=VIEW_ENVIRONMENT, environment=environment
        )
