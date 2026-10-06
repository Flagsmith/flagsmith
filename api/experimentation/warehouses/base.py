from __future__ import annotations

import typing
from collections.abc import Mapping
from typing import Any, Protocol

if typing.TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from experimentation.dataclasses import (
        ExposureBucket,
        MetricSpec,
        ResultsAggregates,
        WarehouseEventNames,
        WarehouseEventStats,
    )
    from experimentation.models import WarehouseConnection
    from experimentation.types import ExposureGranularity


class Warehouse(Protocol):
    def validate_config(
        self,
        config: dict[str, Any],
        *,
        stored: dict[str, Any] | None = None,
    ) -> Mapping[str, Any] | None:
        """Return the configuration to store, merged over ``stored``."""

    def validate_credentials(self, credentials: dict[str, Any]) -> Mapping[str, Any]:
        """Return the credentials to store."""

    def verify(self, connection: WarehouseConnection) -> None:
        """Raise if the connection cannot be used to deliver events."""

    def describe_error(self, error: Exception) -> str:
        """Describe a failed verification without leaking driver messages."""

    def get_event_names(
        self,
        connection: WarehouseConnection,
        environment_key: str,
    ) -> WarehouseEventNames | None:
        """Distinct event names received, or None when unreachable."""

    def get_event_stats(
        self,
        connection: WarehouseConnection,
        environment_key: str,
    ) -> WarehouseEventStats | None:
        """Event counts received, or None when unreachable."""

    def get_exposure_buckets(
        self,
        connection: WarehouseConnection,
        *,
        environment_key: str,
        feature_name: str,
        window_start: datetime,
        window_end: datetime,
        granularity: ExposureGranularity,
    ) -> list[ExposureBucket]:
        """First exposures per variant and time bucket in the window."""

    def get_results_aggregates(
        self,
        connection: WarehouseConnection,
        *,
        environment_key: str,
        feature_name: str,
        window_start: datetime,
        window_end: datetime,
        specs: Sequence[MetricSpec],
        granularity: ExposureGranularity,
    ) -> ResultsAggregates:
        """Metric statistics and chart rows behind one results refresh."""
