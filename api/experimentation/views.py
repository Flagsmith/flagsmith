from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from environments.models import Environment
from experimentation.models import WarehouseConnection
from experimentation.permissions import WarehouseConnectionPermission
from experimentation.serializers import WarehouseConnectionSerializer
from experimentation.services import create_warehouse_audit_log
from users.models import FFAdminUser


class WarehouseConnectionView(APIView):
    permission_classes = [IsAuthenticated, WarehouseConnectionPermission]

    def _get_user(self, request: Request) -> FFAdminUser:
        return request.user  # type: ignore[return-value]

    def get(self, request: Request, environment_api_key: str) -> Response:
        environment = get_object_or_404(Environment, api_key=environment_api_key)
        connections = WarehouseConnection.objects.filter(environment=environment)
        return Response(WarehouseConnectionSerializer(connections, many=True).data)

    def post(self, request: Request, environment_api_key: str) -> Response:
        environment = get_object_or_404(Environment, api_key=environment_api_key)

        serializer = WarehouseConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        warehouse_type = serializer.validated_data["warehouse_type"]
        if WarehouseConnection.objects.filter(
            environment=environment,
            warehouse_type=warehouse_type,
        ).exists():
            return Response(
                {"detail": "Warehouse connection already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        connection = serializer.save(environment=environment)
        create_warehouse_audit_log(
            connection, self._get_user(request), action="created"
        )
        return Response(
            WarehouseConnectionSerializer(connection).data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request: Request, environment_api_key: str) -> Response:
        environment = get_object_or_404(Environment, api_key=environment_api_key)
        connection = WarehouseConnection.objects.filter(
            environment=environment,
        ).first()
        if connection is None:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        create_warehouse_audit_log(
            connection, self._get_user(request), action="deleted"
        )
        connection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
