from django.db.models import Q
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.serializers import ErrorSerializer
from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from environments.permissions.permissions import HasEnvironmentPermission
from features.workflows.serializers import (
    ChangeRequestListQuerySerializer,
    ChangeRequestListSerializer,
    CreateChangeRequestSerializer,
)


class CreateChangeRequestMixin:
    def get_permissions(self):
        if self.action == "create_change_request":
            return (
                IsAuthenticated(),
                HasEnvironmentPermission(
                    environment_permissions=[UPDATE_FEATURE_STATE]
                ),
            )

        return super().get_permissions()

    @swagger_auto_schema(
        method="POST",
        request_body=CreateChangeRequestSerializer(),
        responses={201: CreateChangeRequestSerializer(), 400: ErrorSerializer()},
    )
    @action(detail=True, methods=["POST"], url_path="create-change-request")
    def create_change_request(self, request: Request, **kwargs) -> Response:
        serializer = CreateChangeRequestSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(environment=self.get_object(), user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ListChangeRequestsMixin:
    def get_permissions(self):
        if self.action == "list_change_requests":
            return (
                IsAuthenticated(),
                HasEnvironmentPermission(environment_permissions=[VIEW_ENVIRONMENT]),
            )

        return super().get_permissions()

    @swagger_auto_schema(
        method="GET",
        responses={200: ChangeRequestListSerializer(), 400: ErrorSerializer()},
        query_serializer=ChangeRequestListQuerySerializer(),
    )
    @action(detail=True, methods=["GET"], url_path="list-change-requests")
    def list_change_requests(self, request: Request, **kwargs) -> Response:
        environment = self.get_object()
        serializer = ChangeRequestListSerializer(
            instance=environment.change_requests.filter(
                self._get_queryset_filter_from_query_params(),
                deleted_at__isnull=True,
            ),
            many=True,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_queryset_filter_from_query_params(self) -> Q:
        query_serializer = ChangeRequestListQuerySerializer(
            data=self.request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        query_filters = query_serializer.data

        q = Q()

        if not query_filters.get("include_committed"):
            q = q & Q(committed_at__isnull=True)

        if query_filters.get("search"):
            q = q & Q(title__icontains=query_filters["search"])

        return q
