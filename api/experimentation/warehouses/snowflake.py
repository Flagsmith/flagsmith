from __future__ import annotations

import base64
import hashlib
import math
import re
import time
import typing
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, suppress
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from rest_framework import serializers

from experimentation.types import (
    SNOWFLAKE_DEFAULTS,
    SnowflakeConfig,
    SnowflakeCredentials,
)
from experimentation.warehouses.exceptions import (
    DeliveryConfigError,
    UnsupportedWarehouseOperation,
)
from experimentation.warehouses.queries import QueryResult

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

    from experimentation.dataclasses import (
        ExposureBucket,
        MetricSpec,
        ResultsAggregates,
        WarehouseEventNames,
        WarehouseEventStats,
    )
    from experimentation.models import WarehouseConnection
    from experimentation.types import ExposureGranularity

_ACCOUNT_IDENTIFIER = re.compile(r"[A-Za-z0-9_-]+")
_PLACEHOLDER = re.compile(r"%\((\w+)\)s")
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

CONNECT_TIMEOUT_SECONDS = 5
POLL_INTERVAL_SECONDS = 1
MIN_STATEMENT_TIMEOUT_SECONDS = 1
JWT_LIFETIME_SECONDS = 59 * 60
USER_AGENT = "Flagsmith"


class SnowflakeAuthError(Exception):
    pass


class SnowflakeTimeout(Exception):
    pass


class SnowflakeRequestError(Exception):
    def __init__(
        self,
        status_code: int | None,
        error_code: str | None,
        sql_state: str | None = None,
    ) -> None:
        super().__init__(
            f"Snowflake request failed: {status_code} {error_code} {sql_state}"
        )
        self.status_code = status_code
        self.error_code = error_code
        self.sql_state = sql_state


def _to_binding(name: str, value: object) -> dict[str, str]:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError(f"Parameter {name} must be timezone-aware.")
        nanoseconds = (value - _EPOCH) // timedelta(microseconds=1) * 1000
        return {"type": "TIMESTAMP_NTZ", "value": str(nanoseconds)}
    if isinstance(value, bool):
        raise TypeError(f"Unsupported parameter type for {name}: bool")
    if isinstance(value, int):
        return {"type": "FIXED", "value": str(value)}
    if isinstance(value, float):
        return {"type": "REAL", "value": str(value)}
    if isinstance(value, str):
        return {"type": "TEXT", "value": value}
    raise TypeError(f"Unsupported parameter type for {name}: {type(value).__name__}")


def _rewrite_to_positional_bindings(
    statement: str, params: Mapping[str, object]
) -> tuple[str, dict[str, dict[str, str]]]:
    bindings: dict[str, dict[str, str]] = {}

    def bind(match: re.Match[str]) -> str:
        name = match.group(1)
        bindings[str(len(bindings) + 1)] = _to_binding(name, params[name])
        return "?"

    return _PLACEHOLDER.sub(bind, statement), bindings


def _parse_epoch_seconds(value: str) -> datetime:
    return _EPOCH + timedelta(microseconds=int(Decimal(value) * 1_000_000))


_CONVERTERS: dict[str, Callable[[str], object]] = {
    "real": float,
    "text": str,
    "boolean": lambda value: value == "true",
    "timestamp_ntz": _parse_epoch_seconds,
    "timestamp_ltz": _parse_epoch_seconds,
}


def _column_converter(column: dict[str, Any]) -> Callable[[str], object]:
    if column["type"] == "fixed":
        return int if column["scale"] == 0 else float
    return _CONVERTERS[column["type"]]


def _convert_rows(payload: dict[str, Any]) -> QueryResult:
    metadata = payload["resultSetMetaData"]
    if len(metadata.get("partitionInfo") or []) > 1:
        raise SnowflakeRequestError(None, "MULTI_PARTITION_RESULT")
    columns = metadata["rowType"]
    converters = [_column_converter(column) for column in columns]
    rows = [
        [
            None if value is None else convert(value)
            for convert, value in zip(converters, row)
        ]
        for row in payload.get("data") or []
    ]
    return QueryResult(rows, [column["name"].lower() for column in columns])


def _sign_jwt(config: SnowflakeConfig, credentials: SnowflakeCredentials) -> str:
    try:
        private_key = serialization.load_pem_private_key(
            credentials["private_key"].encode(), password=None
        )
    except (ValueError, TypeError) as exc:
        raise SnowflakeAuthError() from exc
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise SnowflakeAuthError()
    public_key_der = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    fingerprint = base64.b64encode(hashlib.sha256(public_key_der).digest()).decode()
    qualified_user = f"{config['account_identifier']}.{config['user']}".upper()
    issued_at = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "iss": f"{qualified_user}.SHA256:{fingerprint}",
            "sub": qualified_user,
            "iat": issued_at,
            "exp": issued_at + timedelta(seconds=JWT_LIFETIME_SECONDS),
        },
        private_key,
        algorithm="RS256",
    )


class _Session:
    def __init__(
        self,
        http: requests.Session,
        config: SnowflakeConfig,
        credentials: SnowflakeCredentials,
        deadline: float,
    ) -> None:
        self._http = http
        self._config = config
        host = config["account_identifier"].lower().replace("_", "-")
        self._base_url = f"https://{host}.snowflakecomputing.com"
        self._deadline = deadline
        self._headers = {
            "Authorization": f"Bearer {_sign_jwt(config, credentials)}",
            "X-Snowflake-Authorization-Token-Type": "KEYPAIR_JWT",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }

    def _remaining(self) -> float:
        return self._deadline - time.monotonic()

    def _request(
        self, method: str, path: str, *, read_timeout: float, **kwargs: Any
    ) -> requests.Response:
        response = self._http.request(
            method,
            f"{self._base_url}{path}",
            headers=self._headers,
            timeout=(CONNECT_TIMEOUT_SECONDS, read_timeout),
            allow_redirects=False,
            **kwargs,
        )
        if response.status_code not in (200, 202):
            try:
                error = response.json()
            except ValueError:
                error = {}
            raise SnowflakeRequestError(
                response.status_code, error.get("code"), error.get("sqlState")
            )
        return response

    def run(self, statement: str, params: Mapping[str, object]) -> QueryResult:
        positional_statement, bindings = _rewrite_to_positional_bindings(
            statement, params
        )
        statement_timeout_seconds = max(
            math.ceil(self._remaining()), MIN_STATEMENT_TIMEOUT_SECONDS
        )
        try:
            response = self._request(
                "POST",
                "/api/v2/statements",
                read_timeout=statement_timeout_seconds + CONNECT_TIMEOUT_SECONDS,
                params={"requestId": str(uuid.uuid4())},
                json={
                    "statement": positional_statement,
                    "timeout": statement_timeout_seconds,
                    "database": self._config["database"],
                    "schema": self._config["schema"],
                    "warehouse": self._config["warehouse"],
                    "role": self._config["role"],
                    "bindings": bindings,
                    "parameters": {"timezone": "UTC"},
                },
            )
            statement_handle = response.json()["statementHandle"]
            while response.status_code == 202:
                if self._remaining() <= 0:
                    with suppress(requests.RequestException, SnowflakeRequestError):
                        self._request(
                            "POST",
                            f"/api/v2/statements/{statement_handle}/cancel",
                            read_timeout=CONNECT_TIMEOUT_SECONDS,
                        )
                    raise SnowflakeTimeout()
                time.sleep(POLL_INTERVAL_SECONDS)
                try:
                    response = self._request(
                        "GET",
                        f"/api/v2/statements/{statement_handle}",
                        read_timeout=max(self._remaining(), 1),
                    )
                except (requests.Timeout, requests.ConnectionError):
                    continue
        except SnowflakeRequestError as exc:
            if exc.status_code == 401:
                raise SnowflakeAuthError() from exc
            if exc.status_code == 408:
                raise SnowflakeTimeout() from exc
            raise
        return _convert_rows(response.json())


@contextmanager
def snowflake_session(
    connection: WarehouseConnection, *, budget_seconds: float
) -> Iterator[_Session]:
    """Yield a session holding one signed JWT, for every statement of one operation."""
    config = typing.cast(SnowflakeConfig, connection.config or {})
    credentials = typing.cast(SnowflakeCredentials, connection.credentials or {})
    if not (
        SnowflakeConfig.__required_keys__ <= config.keys()
        and SnowflakeCredentials.__required_keys__ <= credentials.keys()
    ):
        raise DeliveryConfigError("Stored connection details are incomplete.")
    if not _ACCOUNT_IDENTIFIER.fullmatch(config["account_identifier"]):
        raise DeliveryConfigError(
            "Account identifier must contain only letters, digits, hyphens and underscores."
        )
    with requests.Session() as http:
        yield _Session(http, config, credentials, time.monotonic() + budget_seconds)


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
        raise UnsupportedWarehouseOperation("Snowflake results are not supported.")

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
        raise UnsupportedWarehouseOperation("Snowflake results are not supported.")
