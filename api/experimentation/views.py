from typing import Any

from django.db.models import QuerySet
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from environments.views import NestedEnvironmentViewSet
from experimentation.models import (
    Experiment,
    ExperimentStatus,
    WarehouseConnection,
)
from experimentation.permissions import (
    ExperimentPermission,
    WarehouseConnectionPermission,
)
from experimentation.serializers import (
    ExperimentSerializer,
    WarehouseConnectionSerializer,
)
from experimentation.services import (
    create_experiment_audit_log,
    create_warehouse_audit_log,
    transition_experiment_status,
)
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

        if WarehouseConnection.objects.filter(
            environment=environment,
        ).exists():
            return Response(
                {
                    "detail": "This environment already has an active warehouse connection."
                },
                status=409,
            )

        self.perform_create(serializer)
        return Response(serializer.data, status=201)

    @staticmethod
    def _get_user(request: Request) -> FFAdminUser:
        return request.user  # type: ignore[return-value]


class ExperimentViewSet(
    NestedEnvironmentViewSet[Experiment],
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = ExperimentSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, ExperimentPermission]
    model_class = Experiment
    lookup_field = "id"
    lookup_url_kwarg = "experiment_id"
    filterset_fields: list[str] = []

    def get_serializer_context(self) -> dict[str, Any]:
        context = super().get_serializer_context()
        context["environment"] = self._get_environment()
        return context

    def get_queryset(self) -> "QuerySet[Experiment]":
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        feature = serializer.validated_data["feature"]
        environment = self._get_environment()
        if (
            Experiment.objects.filter(
                feature=feature,
                environment=environment,
            )
            .exclude(status=ExperimentStatus.COMPLETED)
            .exists()
        ):
            return Response(
                {"detail": "An active experiment already exists for this feature."},
                status=409,
            )

        self.perform_create(serializer)
        return Response(serializer.data, status=201)

    def perform_create(self, serializer: BaseSerializer[Experiment]) -> None:
        experiment: Experiment = serializer.save(environment=self._get_environment())
        create_experiment_audit_log(
            experiment, self._get_user(self.request), action="created"
        )

    def perform_update(self, serializer: BaseSerializer[Experiment]) -> None:
        experiment: Experiment = serializer.save()
        create_experiment_audit_log(
            experiment, self._get_user(self.request), action="updated"
        )

    def perform_destroy(self, instance: Experiment) -> None:
        create_experiment_audit_log(
            instance, self._get_user(self.request), action="deleted"
        )
        instance.delete()

    @action(detail=True, methods=["post"])
    def start(self, request: Request, **kwargs: object) -> Response:
        return self._transition_status(ExperimentStatus.RUNNING)

    @action(detail=True, methods=["post"])
    def pause(self, request: Request, **kwargs: object) -> Response:
        return self._transition_status(ExperimentStatus.PAUSED)

    @action(detail=True, methods=["post"])
    def complete(self, request: Request, **kwargs: object) -> Response:
        return self._transition_status(ExperimentStatus.COMPLETED)

    def _transition_status(self, target_status: str) -> Response:
        experiment: Experiment = self.get_object()
        try:
            experiment = transition_experiment_status(
                experiment, target_status, self._get_user(self.request)
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        serializer = self.get_serializer(experiment)
        return Response(serializer.data)

    @staticmethod
    def _get_user(request: Request) -> FFAdminUser:
        return request.user  # type: ignore[return-value]
