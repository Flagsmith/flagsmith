from __future__ import annotations

import typing
from collections.abc import Mapping
from typing import Any, Protocol

if typing.TYPE_CHECKING:
    from experimentation.dataclasses import WarehouseEventNames, WarehouseEventStats
    from experimentation.models import WarehouseConnection


class UnsupportedWarehouseOperation(Exception):
    """Raised before any side effect when a warehouse type lacks an operation."""


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
