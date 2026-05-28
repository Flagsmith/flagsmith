import logging
from typing import Any

from django.db import IntegrityError
from django.db.models import Q, QuerySet
from rest_framework import mixins, serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from app.pagination import CustomPagination
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
    ExperimentListSerializer,
    ExperimentSerializer,
    WarehouseConnectionSerializer,
)
from experimentation.services import (
    create_experiment_audit_log,
    create_warehouse_audit_log,
    transition_experiment_status,
)
from users.models import FFAdminUser

logger = logging.getLogger(__name__)


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
                status=status.HTTP_409_CONFLICT,
            )

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, ExperimentPermission]
    model_class = Experiment
    lookup_field = "id"
    lookup_url_kwarg = "experiment_id"

    def get_serializer_context(self) -> dict[str, Any]:
        context = super().get_serializer_context()
        context["environment"] = self._get_environment()
        return context

    def get_serializer_class(self) -> type[BaseSerializer[Experiment]]:
        if self.action in ("list", "retrieve", "start", "pause", "complete"):
            return ExperimentListSerializer
        return ExperimentSerializer

    def get_queryset(self) -> "QuerySet[Experiment]":
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            qs = qs.select_related("feature").prefetch_related(
                "feature__multivariate_options"
            )
        status_filter = self.request.query_params.get("status")
        if status_filter:
            if status_filter not in ExperimentStatus.values:
                raise serializers.ValidationError(
                    {"status": f"Invalid status '{status_filter}'."}
                )
            qs = qs.filter(status=status_filter)

        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(feature__name__icontains=q))

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
                status=status.HTTP_409_CONFLICT,
            )

        try:
            self.perform_create(serializer)
        except IntegrityError:
            return Response(
                {"detail": "An active experiment already exists for this feature."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer: BaseSerializer[Experiment]) -> None:
        experiment: Experiment = serializer.save(environment=self._get_environment())
        create_experiment_audit_log(
            experiment, self._get_user(self.request), action="created"
        )

    def perform_update(self, serializer: BaseSerializer[Experiment]) -> None:
        changed_fields = {
            field
            for field, value in serializer.validated_data.items()
            if getattr(serializer.instance, field, None) != value
        }
        if not changed_fields:
            return
        experiment: Experiment = serializer.save()
        create_experiment_audit_log(
            experiment, self._get_user(self.request), action="updated"
        )

    def perform_destroy(self, instance: Experiment) -> None:
        if instance.status == ExperimentStatus.RUNNING:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Cannot delete a running experiment. "
                        "Pause or complete it first."
                    )
                }
            )
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
        except ValueError:
            logger.warning(
                "Invalid experiment status transition for "
                "experiment_id=%s to status=%s",
                experiment.id,
                target_status,
                exc_info=True,
            )
            return Response(
                {"detail": "Unable to transition experiment status."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(experiment)
        return Response(serializer.data)

    @staticmethod
    def _get_user(request: Request) -> FFAdminUser:
        return request.user  # type: ignore[return-value]
