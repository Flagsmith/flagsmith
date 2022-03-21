from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from features.workflows.models import ChangeRequest
from features.workflows.permissions import ChangeRequestPermissions
from features.workflows.serializers import (
    ChangeRequestListQuerySerializer,
    ChangeRequestSerializer,
)


class ChangeRequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated, ChangeRequestPermissions)
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
            "from_feature_state__environment__project",
            "from_feature_state__environment__project__organisation",
            "to_feature_state",
            "user",
            "committed_by",
        ).prefetch_related("approvals")

    @action(detail=True, methods=["POST"])
    def approve(self, request: Request, pk: int = None) -> Response:
        change_request = self.get_object()
        change_request.approve(user=request.user)
        return Response(self.get_serializer(instance=change_request).data)

    @action(detail=True, methods=["POST"])
    def commit(self, request: Request, pk: int = None) -> Response:
        change_request = self.get_object()
        change_request.commit(committed_by=request.user)
        return Response(self.get_serializer(instance=change_request).data)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()
