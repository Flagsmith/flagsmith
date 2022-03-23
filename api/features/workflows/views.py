from core.serializers import EmptySerializer
from django.utils import timezone
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.serializers import ErrorSerializer
from features.workflows.models import ChangeRequest
from features.workflows.permissions import ChangeRequestPermissions
from features.workflows.serializers import (
    ChangeRequestListQuerySerializer,
    ChangeRequestListSerializer,
    ChangeRequestRetrieveSerializer,
    CreateChangeRequestSerializer,
)


class ChangeRequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated, ChangeRequestPermissions)
    serializer_class = CreateChangeRequestSerializer

    def get_queryset(self):
        queryset = ChangeRequest.objects.filter(deleted_at__isnull=True)

        if self.action == "list":
            queryset = self._apply_query_filters(queryset)

        return queryset.select_related("user", "committed_by").prefetch_related(
            "approvals"
        )

    def _apply_query_filters(self, queryset):
        query_serializer = ChangeRequestListQuerySerializer(
            data=self.request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        query_filters = query_serializer.data

        queryset = queryset.filter(environment=query_filters["environment"])

        if not query_filters.get("include_committed"):
            queryset.filter(committed_at__isnull=True)

        if query_filters.get("search"):
            queryset.filter(title__icontains=query_filters["search"])

        return queryset

    def get_serializer_class(self):
        return {
            "retrieve": ChangeRequestRetrieveSerializer,
            "update": CreateChangeRequestSerializer,
            "partial_update": CreateChangeRequestSerializer,
            "approve": ChangeRequestRetrieveSerializer,
            "commit": ChangeRequestRetrieveSerializer,
        }.get(self.action, ChangeRequestListSerializer)

    @swagger_auto_schema(
        method="POST",
        request_body=EmptySerializer(),
        responses={
            200: ChangeRequestRetrieveSerializer(),
            400: ErrorSerializer(),
            403: ErrorSerializer(),
        },
    )
    @action(detail=True, methods=["POST"])
    def approve(self, request: Request, pk: int = None) -> Response:
        change_request = self.get_object()
        change_request.approve(user=request.user)
        return Response(self.get_serializer(instance=change_request).data)

    @swagger_auto_schema(
        method="POST",
        request_body=EmptySerializer(),
        responses={
            200: ChangeRequestRetrieveSerializer(),
            400: ErrorSerializer(),
            403: ErrorSerializer(),
        },
    )
    @action(detail=True, methods=["POST"])
    def commit(self, request: Request, pk: int = None) -> Response:
        change_request = self.get_object()
        change_request.commit(committed_by=request.user)
        return Response(self.get_serializer(instance=change_request).data)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()
