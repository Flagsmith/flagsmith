from typing import Any, Callable

from django.conf import settings
from rest_framework import serializers

from experimentation.models import WarehouseConnection, WarehouseType
from experimentation.types import (
    CLICKHOUSE_DEFAULTS,
    SNOWFLAKE_DEFAULTS,
    ClickHouseConfig,
    ClickHouseCredentials,
    SnowflakeConfig,
)


def validate_clickhouse_credentials(
    credentials: dict[str, Any],
) -> ClickHouseCredentials:
    if not isinstance(credentials, dict):
        raise serializers.ValidationError({"credentials": "Must be an object."})
    password = credentials.get("password")
    if not password or not isinstance(password, str):
        raise serializers.ValidationError(
            {"credentials": {"password": "This field is required."}}
        )
    return {"password": password}


def validate_clickhouse_config(config: dict[str, Any]) -> ClickHouseConfig:
    if not isinstance(config, dict):
        raise serializers.ValidationError({"config": "Must be an object."})
    if not config.get("host"):
        raise serializers.ValidationError(
            {"config": {"host": "This field is required."}}
        )
    merged: ClickHouseConfig = {
        **CLICKHOUSE_DEFAULTS,
        **config,  # type: ignore[typeddict-item]
    }
    port = merged["port"]
    if isinstance(port, bool) or not isinstance(port, int) or not (1 <= port <= 65535):
        raise serializers.ValidationError(
            {"config": {"port": "Enter a valid port number (1-65535)."}}
        )
    return merged


def validate_snowflake_config(config: dict[str, Any]) -> SnowflakeConfig:
    account_identifier = config.get("account_identifier", "")
    if not account_identifier:
        raise serializers.ValidationError(
            {"config": {"account_identifier": "This field is required."}}
        )
    merged: SnowflakeConfig = {
        **SNOWFLAKE_DEFAULTS,
        **config,  # type: ignore[typeddict-item]
    }
    return merged


CONFIG_VALIDATORS: dict[str, Callable[[dict[str, Any]], Any]] = {
    WarehouseType.SNOWFLAKE: validate_snowflake_config,
    WarehouseType.CLICKHOUSE: validate_clickhouse_config,
}

CREDENTIAL_VALIDATORS: dict[str, Callable[[dict[str, Any]], Any]] = {
    WarehouseType.CLICKHOUSE: validate_clickhouse_credentials,
}


def validate_credentials(
    attrs: dict[str, Any],
    warehouse_type: str,
    instance: WarehouseConnection | None,
) -> None:
    validator = CREDENTIAL_VALIDATORS.get(warehouse_type)
    credentials: dict[str, Any] | None = attrs.get("credentials")
    if validator is None:
        if credentials is not None:
            raise serializers.ValidationError(
                {"credentials": "Only ClickHouse connections accept credentials."}
            )
        if instance is not None and instance.credentials is not None:
            attrs["credentials"] = None
        return
    if settings.SECRET_KEY_IS_EPHEMERAL:
        raise serializers.ValidationError(
            {
                "credentials": (
                    "Storing credentials requires the DJANGO_SECRET_KEY "
                    "environment variable to be set."
                )
            }
        )
    if (
        credentials is None
        and instance is not None
        and instance.warehouse_type == warehouse_type
    ):
        attrs.pop("credentials", None)
        return
    attrs["credentials"] = validator(credentials or {})
