from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from features.workflows.models import ChangeRequest
from features.workflows.serializers import (
    ChangeRequestListQuerySerializer,
    ChangeRequestSerializer,
)


class ChangeRequestViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)  # TODO: permissions
    serializer_class = ChangeRequestSerializer

    def get_queryset(self):
        queryset = ChangeRequest.objects.all()

        if self.action == "list":
            query_serializer = ChangeRequestListQuerySerializer(
                data=self.request.query_params
            )
            query_serializer.is_valid(raise_exception=True)
            queryset = queryset.filter(**query_serializer.data)

        return queryset

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
