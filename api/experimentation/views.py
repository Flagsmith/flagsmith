from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from environments.views import NestedEnvironmentViewSet
from experimentation.models import WarehouseConnection
from experimentation.permissions import WarehouseConnectionPermission
from experimentation.serializers import WarehouseConnectionSerializer
from experimentation.services import create_warehouse_audit_log
from users.models import FFAdminUser


class WarehouseConnectionViewSet(
    NestedEnvironmentViewSet[WarehouseConnection],
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = WarehouseConnectionSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, WarehouseConnectionPermission]
    model_class = WarehouseConnection
    lookup_field = "id"
    lookup_url_kwarg = "connection_id"

    def perform_create(self, serializer: BaseSerializer[WarehouseConnection]) -> None:
        connection: WarehouseConnection = serializer.save(
            environment=self._get_environment()
        )
        create_warehouse_audit_log(
            connection, self._get_user(self.request), action="created"
        )

    def perform_update(self, serializer: BaseSerializer[WarehouseConnection]) -> None:
        connection: WarehouseConnection = serializer.save()
        create_warehouse_audit_log(
            connection, self._get_user(self.request), action="updated"
        )

    def perform_destroy(self, instance: WarehouseConnection) -> None:
        create_warehouse_audit_log(
            instance, self._get_user(self.request), action="deleted"
        )
        instance.delete()

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        environment = self._get_environment()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        warehouse_type = serializer.validated_data["warehouse_type"]
        if WarehouseConnection.objects.filter(
            environment=environment,
            warehouse_type=warehouse_type,
        ).exists():
            return Response(
                {"detail": "Warehouse connection already exists."},
                status=409,
            )

        self.perform_create(serializer)
        return Response(serializer.data, status=201)

    @staticmethod
    def _get_user(request: Request) -> FFAdminUser:
        return request.user  # type: ignore[return-value]
