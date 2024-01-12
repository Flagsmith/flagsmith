from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet

from environments.models import Environment
from environments.permissions.constants import VIEW_ENVIRONMENT

from .serializers import (
    ConversionEventTypeQuerySerializer,
    SplitTestQuerySerializer,
)


class SplitTestPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: ModelViewSet) -> bool:
        if not super().has_permission(request, view):
            return False

        query_serializer = SplitTestQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        environment = get_object_or_404(
            Environment,
            conversion_event_types__id=query_serializer.validated_data[
                "conversion_event_type_id"
            ],
        )

        return request.user.has_environment_permission(
            permission=VIEW_ENVIRONMENT, environment=environment
        )


class ConversionEventTypePermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: ListAPIView) -> bool:
        if not super().has_permission(request, view):
            return False

        query_serializer = ConversionEventTypeQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        environment = get_object_or_404(
            Environment, id=query_serializer.validated_data["environment_id"]
        )

        return request.user.has_environment_permission(
            permission=VIEW_ENVIRONMENT, environment=environment
        )
