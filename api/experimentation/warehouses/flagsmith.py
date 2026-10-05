from __future__ import annotations

import typing
from typing import Any

from rest_framework import serializers

from experimentation.warehouses.exceptions import UnsupportedWarehouseOperation

if typing.TYPE_CHECKING:
    from experimentation.dataclasses import WarehouseEventNames, WarehouseEventStats
    from experimentation.models import WarehouseConnection


class FlagsmithWarehouse:
    def validate_config(
        self,
        config: dict[str, Any],
        *,
        stored: dict[str, Any] | None = None,
    ) -> None:
        if config:
            raise serializers.ValidationError(
                {"config": "Flagsmith warehouse does not accept configuration."}
            )
        return None

    def validate_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        raise UnsupportedWarehouseOperation(
            "Flagsmith connections take no credentials."
        )

    def verify(self, connection: WarehouseConnection) -> None:
        raise UnsupportedWarehouseOperation("Flagsmith connections are not verified.")

    def describe_error(self, error: Exception) -> str:
        raise UnsupportedWarehouseOperation("Flagsmith connections are not verified.")

    def get_event_names(
        self,
        connection: WarehouseConnection,
        environment_key: str,
    ) -> WarehouseEventNames | None:
        raise UnsupportedWarehouseOperation("Served by experimentation.services.")

    def get_event_stats(
        self,
        connection: WarehouseConnection,
        environment_key: str,
    ) -> WarehouseEventStats | None:
        raise UnsupportedWarehouseOperation("Served by experimentation.services.")
