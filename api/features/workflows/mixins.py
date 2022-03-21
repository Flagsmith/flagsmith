from drf_yasg2.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from api.serializers import ErrorSerializer
from features.workflows.serializers import ChangeRequestSerializer


class CreateChangeRequestMixin:
    @swagger_auto_schema(
        method="POST",
        request_body=ChangeRequestSerializer(),
        responses={201: ChangeRequestSerializer(), 400: ErrorSerializer()},
    )
    @action(detail=True, methods=["POST"], url_path="create-change-request")
    def create_change_request(self, request: Request, **kwargs) -> Response:
        serializer = ChangeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(from_feature_state=self.get_object(), user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
