from typing import Any, Callable, cast

from rest_framework import serializers

from core.network import is_internal_address
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


def validate_clickhouse_config(
    config: dict[str, Any],
    *,
    stored: dict[str, Any] | None = None,
) -> ClickHouseConfig:
    if not isinstance(config, dict):
        raise serializers.ValidationError({"config": "Must be an object."})
    if unknown_keys := set(config) - set(CLICKHOUSE_DEFAULTS):
        raise serializers.ValidationError(
            {"config": {key: "Unknown field." for key in sorted(unknown_keys)}}
        )
    base = stored if stored is not None else dict(CLICKHOUSE_DEFAULTS)
    merged: dict[str, Any] = {**base, **config}
    if not merged["host"] or not isinstance(merged["host"], str):
        raise serializers.ValidationError(
            {"config": {"host": "This field is required."}}
        )
    if is_internal_address(merged["host"], include_shared=True):
        raise serializers.ValidationError(
            {
                "config": {
                    "host": (
                        "Host must not target internal or private network addresses."
                    )
                }
            }
        )
    port = merged["port"]
    if isinstance(port, bool) or not isinstance(port, int) or not (1 <= port <= 65535):
        raise serializers.ValidationError(
            {"config": {"port": "Enter a valid port number (1-65535)."}}
        )
    for key in ("database", "username"):
        if not merged[key] or not isinstance(merged[key], str):
            raise serializers.ValidationError(
                {"config": {key: "Must be a non-empty string."}}
            )
    if not isinstance(merged["secure"], bool):
        raise serializers.ValidationError({"config": {"secure": "Must be a boolean."}})
    return cast(ClickHouseConfig, merged)


def validate_snowflake_config(
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
            raise serializers.ValidationError({"config": {key: "Must be a string."}})
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


CONFIG_VALIDATORS: dict[str, Callable[..., Any]] = {
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
    if (
        "credentials" not in attrs
        and instance is not None
        and instance.warehouse_type == warehouse_type
    ):
        return
    attrs["credentials"] = validator(credentials or {})
