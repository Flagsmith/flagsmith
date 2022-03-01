from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from features.workflows.serializers import ChangeRequestSerializer


class ChangeRequestViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)  # TODO: permissions
    serializer_class = ChangeRequestSerializer

    @action(detail=True)
    def add_required_approval(self, request: Request, pk: int = None) -> Response:
        # TODO: add a required approver (should this just be done on create / update?)
        pass

    @action(detail=True)
    def approve(self, request: Request, pk: int = None) -> Response:
        # TODO: tidy up / test this
        change_request = self.get_object()
        change_request.approve(user=request.user)
        return Response(self.get_serializer(instance=change_request).data)

    @action(detail=True)
    def comments(self, request: Request, pk: int = None) -> Response:
        # TODO: list comments
        pass

    @action(detail=True)
    def approvals(self, request: Request, pk: int = None) -> Response:
        # TODO: list approvals
        pass

    def perform_create(self, serializer):
        super().perform_create(serializer)
