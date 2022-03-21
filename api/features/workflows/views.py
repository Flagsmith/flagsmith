from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from environments.models import Environment
from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from environments.permissions.permissions import HasEnvironmentPermission
from features.models import FeatureState
from features.workflows.models import ChangeRequest
from features.workflows.serializers import (
    ChangeRequestListQuerySerializer,
    ChangeRequestSerializer,
)


class ChangeRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ChangeRequestSerializer

    def get_queryset(self):
        queryset = ChangeRequest.objects.filter(deleted_at__isnull=True)

        if self.action == "list":
            query_serializer = ChangeRequestListQuerySerializer(
                data=self.request.query_params
            )
            query_serializer.is_valid(raise_exception=True)
            queryset = queryset.filter(**query_serializer.data)

        return queryset.select_related(
            "from_feature_state",
            "from_feature_state__environment",
            "to_feature_state",
            "user",
            "committed_by",
        )

    def get_permissions(self):
        permission_objects = [IsAuthenticated()]
        required_environment_permissions = []

        if self.action == "list":
            environment_id = self.request.query_params.get("environment")
            environment = Environment.objects.get(id=environment_id)
            required_environment_permissions.append(VIEW_ENVIRONMENT)
        elif self.action == "create":
            feature_state_id = self.request.data.get("from_feature_state")
            environment = FeatureState.objects.get(id=feature_state_id).environment
            required_environment_permissions.append(UPDATE_FEATURE_STATE)
        elif self.action in (
            "update",
            "partial_update",
            "destroy",
            "approve",
            "commit",
        ):
            change_request = self.get_object()
            environment = change_request.from_feature_state.environment
            required_environment_permissions.append(UPDATE_FEATURE_STATE)
        else:
            raise APIException(f"Unknown action: '{self.action}'")

        permission_objects.extend(
            [
                HasEnvironmentPermission(permission, environment)
                for permission in required_environment_permissions
            ]
        )

        return permission_objects

    @action(detail=True, methods=["POST"])
    def approve(self, request: Request, pk: int = None) -> Response:
        change_request = self.get_object()
        change_request.approve(user=request.user)
        return Response(self.get_serializer(instance=change_request).data)

    @action(detail=True, methods=["POST"])
    def commit(self, request: Request, pk: int = None) -> Response:
        change_request = self.get_object()
        change_request.commit()
        return Response(self.get_serializer(instance=change_request).data)

    def perform_create(self, serializer: ChangeRequestSerializer) -> Response:
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()
