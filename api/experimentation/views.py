import logging
from datetime import timedelta
from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import GenericViewSet

from app.pagination import CustomPagination
from core.dataclasses import AuthorData
from environments.views import NestedEnvironmentViewSet
from experimentation.constants import (
    EXPOSURES_REFRESH_MIN_INTERVAL,
    RESULTS_REFRESH_MIN_INTERVAL,
)
from experimentation.models import (
    Experiment,
    ExperimentComputation,
    ExperimentExposures,
    ExperimentMetric,
    ExperimentResults,
    ExperimentStatus,
    Metric,
    WarehouseConnection,
    WarehouseType,
)
from experimentation.permissions import (
    ExperimentPermission,
    MetricPermission,
    WarehouseConnectionPermission,
)
from experimentation.serializers import (
    ExperimentDetailSerializer,
    ExperimentExposuresSerializer,
    ExperimentListSerializer,
    ExperimentMetricSerializer,
    ExperimentQueryParamSerializer,
    ExperimentResultsSerializer,
    ExperimentRolloutSerializer,
    ExperimentSerializer,
    MetricSerializer,
    WarehouseConnectionSerializer,
)
from experimentation.services import (
    annotate_warehouse_event_stats,
    apply_experiment_rollout,
    create_experiment_audit_log,
    create_metric_audit_log,
    create_warehouse_audit_log,
    enable_experiment_rollout,
    mark_warehouse_pending_connection,
    refresh_warehouse_connection_status,
    transition_experiment_status,
)
from experimentation.tasks import (
    compute_experiment_exposures,
    compute_experiment_results,
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
    """Manage data warehouse connections for an environment."""

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

    def list(self, request: Request, *args: object, **kwargs: object) -> Response:
        environment_api_key: str = self.kwargs["environment_api_key"]
        connections = list(self.filter_queryset(self.get_queryset()))
        exclude_event_stats = (
            request.query_params.get("exclude_event_stats", "").lower() == "true"
        )
        if not exclude_event_stats:
            for connection in connections:
                annotate_warehouse_event_stats(connection, environment_api_key)
        serializer = self.get_serializer(connections, many=True)
        return Response(serializer.data)

    def retrieve(self, request: Request, *args: object, **kwargs: object) -> Response:
        connection = self.get_object()
        annotate_warehouse_event_stats(connection, self.kwargs["environment_api_key"])
        serializer = self.get_serializer(connection)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="test-warehouse-connection")
    def test_warehouse_connection(self, request: Request, **kwargs: object) -> Response:
        connection: WarehouseConnection = self.get_object()
        if connection.warehouse_type != WarehouseType.FLAGSMITH:
            return Response(
                {"detail": "Test events are only supported for Flagsmith warehouses."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mark_warehouse_pending_connection(connection)
        annotate_warehouse_event_stats(connection, self.kwargs["environment_api_key"])
        if connection.event_stats is not None:
            refresh_warehouse_connection_status(connection, connection.event_stats)
        serializer = self.get_serializer(connection)
        return Response(serializer.data)

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


@method_decorator(
    name="list",
    decorator=extend_schema(
        tags=["mcp"],
        parameters=[
            OpenApiParameter(
                name="status",
                location=OpenApiParameter.QUERY,
                description="Filter by experiment status (DRAFT, RUNNING, PAUSED, COMPLETED).",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="q",
                location=OpenApiParameter.QUERY,
                description="Search by experiment or feature name.",
                required=False,
                type=str,
            ),
        ],
        operation_id="list_experiments",
        description="(Beta) Lists experiments for an environment. Supports filtering by status and searching by experiment or feature name.",
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="get_experiment",
        description="(Beta) Retrieves experiment details including feature configuration, attached metrics, and rollout state.",
    ),
)
@method_decorator(
    name="create",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="create_experiment",
        description="(Beta) Creates an experiment for a multivariate feature. Metrics can be attached inline. Only one active experiment per feature is allowed.",
    ),
)
@method_decorator(
    name="update",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="update_experiment",
        description="(Beta) Updates an experiment's name or its hypothesis.",
    ),
)
class ExperimentViewSet(
    NestedEnvironmentViewSet[Experiment],
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    """Manage experiments for an environment."""

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
        if self.action == "retrieve":
            return ExperimentDetailSerializer
        if self.action in ("list", "start", "pause", "complete", "rollout"):
            return ExperimentListSerializer
        return ExperimentSerializer

    def get_queryset(self) -> "QuerySet[Experiment]":
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            qs = qs.select_related("feature").prefetch_related(
                "feature__multivariate_options",
                "feature__feature_states__multivariate_feature_state_values",
                "experiment_metrics__metric",
            )
        query_params = ExperimentQueryParamSerializer(data=self.request.GET)
        query_params.is_valid(raise_exception=True)
        if status_filter := query_params.validated_data.get("status"):
            qs = qs.filter(status__in=status_filter)

        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(feature__name__icontains=q))

        return qs.order_by("-created_at")

    def list(self, request: Request, *args: object, **kwargs: object) -> Response:
        response = super().list(request, *args, **kwargs)
        base_qs = super().get_queryset()
        q = request.query_params.get("q")
        if q:
            base_qs = base_qs.filter(
                Q(name__icontains=q) | Q(feature__name__icontains=q)
            )
        counts = base_qs.aggregate(
            **{s.value: Count("id", filter=Q(status=s.value)) for s in ExperimentStatus}
        )
        response.data["status_counts"] = counts
        return response

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
        with transaction.atomic():
            response = self._transition_status(ExperimentStatus.RUNNING)
            if status.is_success(response.status_code):
                enable_experiment_rollout(
                    self.get_object(), AuthorData.from_request(request)
                )
        return response

    @action(detail=True, methods=["post"])
    def pause(self, request: Request, **kwargs: object) -> Response:
        return self._transition_status(ExperimentStatus.PAUSED)

    @action(detail=True, methods=["post"])
    def complete(self, request: Request, **kwargs: object) -> Response:
        return self._transition_status(ExperimentStatus.COMPLETED)

    @action(detail=True, methods=["patch"])
    def rollout(self, request: Request, **kwargs: object) -> Response:
        experiment: Experiment = self.get_object()
        serializer = ExperimentRolloutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        apply_experiment_rollout(
            experiment,
            ExperimentRolloutSerializer.to_spec(serializer.validated_data, request),
        )
        return Response(self.get_serializer(experiment).data)

    @extend_schema(
        tags=["mcp"],
        operation_id="get_experiment_exposures",
        description="(Beta) Retrieves variant exposure counts for an experiment. Returns null if not yet computed.",
    )
    @action(detail=True, methods=["get"])
    def exposures(self, request: Request, **kwargs: object) -> Response:
        experiment: Experiment = self.get_object()
        exposures = getattr(experiment, "exposures", None)
        return Response(
            {
                "exposures": (
                    ExperimentExposuresSerializer(exposures).data if exposures else None
                ),
            }
        )

    @action(detail=True, methods=["post"], url_path="exposures/refresh")
    def refresh_exposures(self, request: Request, **kwargs: object) -> Response:
        experiment: Experiment = self.get_object()
        exposures = ExperimentExposures.objects.filter(experiment=experiment).first()
        self._validate_refresh_request(
            experiment,
            exposures,
            min_interval=EXPOSURES_REFRESH_MIN_INTERVAL,
            before_start_detail="Cannot refresh exposures before the experiment starts.",
            final_detail="Exposures are final for this completed experiment.",
        )
        if exposures is None:
            exposures, _ = ExperimentExposures.objects.get_or_create(
                experiment=experiment
            )
        exposures.record_refresh_request()
        compute_experiment_exposures.delay(kwargs={"experiment_id": experiment.id})
        return Response(status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        tags=["mcp"],
        operation_id="get_experiment_results",
        description="(Beta) Retrieves statistical results for an experiment's metrics. Returns null if not yet computed.",
    )
    @action(detail=True, methods=["get"])
    def results(self, request: Request, **kwargs: object) -> Response:
        experiment: Experiment = self.get_object()
        results = getattr(experiment, "results", None)
        return Response(
            {
                "results": (
                    ExperimentResultsSerializer(results).data if results else None
                ),
            }
        )

    @action(detail=True, methods=["post"], url_path="results/refresh")
    def refresh_results(self, request: Request, **kwargs: object) -> Response:
        experiment: Experiment = self.get_object()
        results = ExperimentResults.objects.filter(experiment=experiment).first()
        self._validate_refresh_request(
            experiment,
            results,
            min_interval=RESULTS_REFRESH_MIN_INTERVAL,
            before_start_detail="Cannot refresh results before the experiment starts.",
            final_detail="Results are final for this completed experiment.",
        )
        if results is None:
            results, _ = ExperimentResults.objects.get_or_create(experiment=experiment)
        results.record_refresh_request()
        compute_experiment_results.delay(kwargs={"experiment_id": experiment.id})
        return Response(status=status.HTTP_202_ACCEPTED)

    def _validate_refresh_request(
        self,
        experiment: Experiment,
        computation: "ExperimentComputation[Any] | None",
        *,
        min_interval: timedelta,
        before_start_detail: str,
        final_detail: str,
    ) -> None:
        if experiment.started_at is None:
            raise ValidationError({"detail": before_start_detail})
        if computation is not None and computation.is_final:
            raise ValidationError({"detail": final_detail})
        if computation is not None and computation.refresh_requested_at is not None:
            retry_after = min_interval - (
                timezone.now() - computation.refresh_requested_at
            )
            if retry_after.total_seconds() > 0:
                raise Throttled(
                    wait=retry_after.total_seconds(),
                    detail="A refresh was requested recently. Try again later.",
                )

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


class ExperimentMetricViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet[ExperimentMetric],
):
    """Manage metrics for an experiment."""

    serializer_class = ExperimentMetricSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, ExperimentPermission]
    lookup_field = "id"
    lookup_url_kwarg = "pk"

    # The nested router derives this kwarg from the parent's lookup_url_kwarg
    # ("experiment_id") plus its "experiment_" nest prefix.
    experiment_url_kwarg = "experiment_experiment_id"

    def get_queryset(self) -> "QuerySet[ExperimentMetric]":
        return ExperimentMetric.objects.filter(
            experiment_id=self.kwargs[self.experiment_url_kwarg],
            experiment__environment__api_key=self.kwargs["environment_api_key"],
        ).select_related("metric")

    def get_serializer_context(self) -> dict[str, Any]:
        context = super().get_serializer_context()
        context["experiment"] = self._get_experiment()
        return context

    def _get_experiment(self) -> Experiment:
        if not hasattr(self, "_experiment"):
            self._experiment = get_object_or_404(
                Experiment,
                id=self.kwargs[self.experiment_url_kwarg],
                environment__api_key=self.kwargs["environment_api_key"],
                deleted_at__isnull=True,
            )
        return self._experiment

    def perform_create(self, serializer: BaseSerializer[ExperimentMetric]) -> None:
        serializer.save(experiment=self._get_experiment())

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        if self._get_experiment().status == ExperimentStatus.COMPLETED:
            return Response(
                {"detail": "Cannot detach metrics from a completed experiment."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


@method_decorator(
    name="list",
    decorator=extend_schema(
        tags=["mcp"],
        parameters=[
            OpenApiParameter(
                name="q",
                location=OpenApiParameter.QUERY,
                description="Search metrics by name.",
                required=False,
                type=str,
            ),
        ],
        operation_id="list_metrics",
        description="(Beta) Lists experiment metrics for an environment. Supports search by name via the q parameter.",
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="get_metric",
        description="(Beta) Retrieves details of a specific metric, including which experiments use it.",
    ),
)
@method_decorator(
    name="create",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="create_metric",
        description="(Beta) Creates a metric with name, description, aggregation type, expected direction, and event definition.",
    ),
)
@method_decorator(
    name="update",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="update_metric",
        description="(Beta) Updates a metric's properties.",
    ),
)
class MetricViewSet(
    NestedEnvironmentViewSet[Metric],
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    """Manage experiment metrics for an environment."""

    serializer_class = MetricSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, MetricPermission]
    model_class = Metric
    lookup_field = "id"
    lookup_url_kwarg = "pk"

    def get_queryset(self) -> "QuerySet[Metric]":
        if getattr(self, "swagger_fake_view", False):
            return super().get_queryset().none()
        qs = (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch(
                    "experiment_metrics",
                    queryset=ExperimentMetric.objects.filter(
                        experiment__deleted_at__isnull=True
                    ).select_related("experiment"),
                )
            )
        )
        if q := self.request.query_params.get("q"):
            qs = qs.filter(name__icontains=q)
        return qs

    def perform_create(self, serializer: BaseSerializer[Metric]) -> None:
        metric: Metric = serializer.save(environment=self._get_environment())
        create_metric_audit_log(metric, self._get_user(self.request), action="created")

    def perform_update(self, serializer: BaseSerializer[Metric]) -> None:
        changed_fields = {
            field
            for field, value in serializer.validated_data.items()
            if getattr(serializer.instance, field, None) != value
        }
        if not changed_fields:
            return
        metric: Metric = serializer.save()
        create_metric_audit_log(metric, self._get_user(self.request), action="updated")

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        instance: Metric = self.get_object()
        if (
            ExperimentMetric.objects.filter(
                metric=instance,
                experiment__deleted_at__isnull=True,
            )
            .exclude(experiment__status=ExperimentStatus.COMPLETED)
            .exists()
        ):
            return Response(
                {
                    "detail": (
                        "Cannot delete a metric attached to an active experiment. "
                        "Detach it or complete the experiment first."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        create_metric_audit_log(instance, self._get_user(request), action="deleted")
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _get_user(request: Request) -> FFAdminUser:
        return request.user  # type: ignore[return-value]
