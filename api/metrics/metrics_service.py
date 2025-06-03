import logging
import time
from typing import Callable

from django.db import models
from django.db.models import Q

from edge_api.identities.models import EdgeIdentity
from environments.models import Environment
from metrics.constants import DEFAULT_METRIC_DEFINITIONS, WORKFLOW_METRIC_DEFINITIONS
from metrics.types import EnvMetricsName, EnvMetricsPayload, MetricDefinition

logger = logging.getLogger(__name__)


class EnvironmentMetricsService:
    def __init__(self, environment: Environment):
        """
        Computes environment-level metrics for an Environment instance.

        This service computes metrics such as:
        - Total and enabled features
        - Segment and identity overrides
        - Open change requests and scheduled changes (if workflows enabled)

        It relies on:
        - Static metric definitions from DEFAULT_METRIC_DEFINITIONS and WORKFLOW_METRIC_DEFINITIONS
        - Predefined queryset methods on the Environment model to fetch metric sources

        Usage:
            service = EnvironmentMetricsService(environment)
            payload = service.get_metrics_payload()

        Notes:
        - Metric order is determined by the "rank" field so the Frontend can consume them without context
        - Uses environment.project.enable_dynamo_db to determine identity override backend
        """
        self.environment = environment
        self.uses_dynamo = environment.project.enable_dynamo_db

    def get_metrics_payload(self) -> EnvMetricsPayload:
        metric_resolvers: dict[EnvMetricsName, Callable[[], int]] = {
            **self._get_segment_metrics(),
            **self._get_identity_metrics(),
            **self._get_feature_metrics(),
        }

        if self.environment.is_workflow_enabled:
            metric_resolvers.update(self._get_workflow_metrics())

        return self._build_payload(metric_resolvers)

    def _get_metric_definitions(self) -> list[MetricDefinition]:
        """
        Returns the list of metrics that are available for the environment.
        """
        definitions = list(DEFAULT_METRIC_DEFINITIONS)
        if self.environment.is_workflow_enabled:
            definitions.extend(WORKFLOW_METRIC_DEFINITIONS)
        return definitions

    def _get_segment_metrics(
        self,
    ) -> dict[EnvMetricsName, Callable[[], int]]:
        """
        Returns a callable that counts the number of segment overrides for the environment.
        """
        return {
            EnvMetricsName.SEGMENT_OVERRIDES: lambda: self.environment.get_segment_metrics_queryset().count(),
        }

    def _get_identity_metrics(self) -> dict[EnvMetricsName, Callable[[], int]]:
        """
        Returns a callable that counts the number of identity overrides for the environment.
        """
        return {
            EnvMetricsName.IDENTITY_OVERRIDES: (
                lambda: EdgeIdentity.dynamo_wrapper.get_identity_overrides_count(
                    self.environment.api_key
                )
            )
            if self.uses_dynamo
            else (lambda: self.environment.get_identity_overrides_queryset().count()),
        }

    def _get_feature_metrics(
        self,
    ) -> dict[EnvMetricsName, Callable[[], int]]:
        """
        Returns callables that counts the total number and enabled count of features for the environment.
        """
        features_qs = self.environment.get_features_metrics_queryset()

        features_aggregation_result: dict[str, int] = features_qs.aggregate(
            total=models.Count("id"),
            enabled=models.Count("id", filter=Q(enabled=True)),
        )
        return {
            EnvMetricsName.TOTAL_FEATURES: lambda: features_aggregation_result["total"],
            EnvMetricsName.ENABLED_FEATURES: lambda: features_aggregation_result[
                "enabled"
            ],
        }

    def _get_workflow_metrics(
        self,
    ) -> dict[EnvMetricsName, Callable[[], int]]:
        """
        Returns callables that counts the number of open change requests and scheduled changes for the environment.
        """
        return {
            EnvMetricsName.OPEN_CHANGE_REQUESTS: lambda: self.environment.get_change_requests_metrics_queryset().count(),
            EnvMetricsName.TOTAL_SCHEDULED_CHANGES: lambda: self.environment.get_scheduled_metrics_queryset().count(),
        }

    def _build_payload(
        self,
        metric_resolvers: dict[EnvMetricsName, Callable[[], int]],
    ) -> EnvMetricsPayload:
        metrics: EnvMetricsPayload = []

        for definition in self._get_metric_definitions():
            name = definition["name"]
            entity = definition["entity"]

            metric_resolver = metric_resolvers[name]
            start = time.perf_counter()
            value = metric_resolver()
            duration = (time.perf_counter() - start) * 1000

            logger.debug(f"[Metrics] {name.value} computed in {duration:.2f}ms")

            metrics.append(
                {
                    **definition,
                    "name": name.value,
                    "entity": entity.value,
                    "value": value,
                }
            )

        return sorted(metrics, key=lambda m: m.get("rank", float("inf")))
