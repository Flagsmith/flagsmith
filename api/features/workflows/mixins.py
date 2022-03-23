from drf_yasg2.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from api.serializers import ErrorSerializer
from features.workflows.serializers import CreateChangeRequestSerializer


class CreateChangeRequestMixin:
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
