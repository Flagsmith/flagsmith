from __future__ import annotations

import typing
from typing import Any

from rest_framework import serializers

from experimentation.types import SNOWFLAKE_DEFAULTS, SnowflakeConfig
from experimentation.warehouses.base import UnsupportedWarehouseOperation

if typing.TYPE_CHECKING:
    from experimentation.dataclasses import WarehouseEventNames, WarehouseEventStats
    from experimentation.models import WarehouseConnection


class SnowflakeWarehouse:
    def validate_config(
        self,
        config: dict[str, Any],
        *,
        stored: dict[str, Any] | None = None,
    ) -> SnowflakeConfig:
        if not isinstance(config, dict):
            raise serializers.ValidationError({"config": "Must be an object."})
        if unknown_keys := set(config) - set(SNOWFLAKE_DEFAULTS):
            raise serializers.ValidationError(
                {"config": {key: "Unknown field." for key in sorted(unknown_keys)}}
            )
        for key, value in config.items():
            if not isinstance(value, str):
                raise serializers.ValidationError(
                    {"config": {key: "Must be a string."}}
                )
        base = stored if stored is not None else dict(SNOWFLAKE_DEFAULTS)
        merged: SnowflakeConfig = {
            **base,  # type: ignore[typeddict-item]
            **config,
        }
        if not merged.get("account_identifier"):
            raise serializers.ValidationError(
                {"config": {"account_identifier": "This field is required."}}
            )
        return merged

    def validate_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        raise UnsupportedWarehouseOperation(
            "Snowflake connections take no credentials."
        )

    def verify(self, connection: WarehouseConnection) -> None:
        raise UnsupportedWarehouseOperation("Snowflake connections cannot be verified.")

    def describe_error(self, error: Exception) -> str:
        raise UnsupportedWarehouseOperation("Snowflake connections cannot be verified.")

    def get_event_names(
        self,
        connection: WarehouseConnection,
        environment_key: str,
    ) -> WarehouseEventNames | None:
        raise UnsupportedWarehouseOperation("Snowflake connections cannot be read.")

    def get_event_stats(
        self,
        connection: WarehouseConnection,
        environment_key: str,
    ) -> WarehouseEventStats | None:
        raise UnsupportedWarehouseOperation("Snowflake connections cannot be read.")
