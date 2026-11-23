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
import structlog
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.cache import cache
from rest_framework import serializers

from experimentation.dataclasses import (
    ExposureBucket,
    ResultsAggregates,
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.types import (
    SNOWFLAKE_DEFAULTS,
    SnowflakeConfig,
    SnowflakeCredentials,
)
from experimentation.warehouses.base import is_disallowed_host
from experimentation.warehouses.cache import (
    CUSTOMER_EVENT_UNAVAILABLE,
    cache_warehouse_read_unless_empty,
    customer_cache_key,
)
from experimentation.warehouses.constants import (
    BACKGROUND_QUERY_TIMEOUT_SECONDS,
    CUSTOMER_EVENT_NAMES_FAILURE_CACHE_SECONDS,
    CUSTOMER_EVENT_STATS_CACHE_SECONDS,
    EVENT_NAMES_CACHE_SECONDS,
    EVENT_NAMES_TIMEOUT_SECONDS,
    MISSING_EVENTS_TABLE_DETAIL,
    PERMISSION_DENIED_DETAIL,
    QUERY_TIMEOUT_DETAIL,
    SCHEMA_MISMATCH_DETAIL,
    VERIFY_TIMEOUT_SECONDS,
)
from experimentation.warehouses.dialect import SNOWFLAKE_DIALECT
from experimentation.warehouses.exceptions import (
    DeliveryConfigError,
    EventsTableSchemaMismatchError,
)
from experimentation.warehouses.queries import (
    QueryResult,
    build_event_names,
    build_event_stats,
    event_names_query,
    event_names_query_params,
    event_stats_query,
    read_exposure_buckets,
    read_results_aggregates,
)

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

    from experimentation.dataclasses import MetricSpec
    from experimentation.models import WarehouseConnection
    from experimentation.types import ExposureGranularity

logger = structlog.get_logger("warehouse")

HOST_SUFFIX = ".snowflakecomputing.com"
_ACCOUNT_IDENTIFIER = re.compile(r"[A-Za-z0-9_-]+")
_ORGANISATION_ACCOUNT_IDENTIFIER = re.compile(r"[A-Za-z0-9]+-[A-Za-z0-9_-]+")
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")
_PLACEHOLDER = re.compile(r"%\((\w+)\)s")
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

CONNECT_TIMEOUT_SECONDS = 5
POLL_INTERVAL_SECONDS = 1
MIN_STATEMENT_TIMEOUT_SECONDS = 1
JWT_LIFETIME_SECONDS = 59 * 60
MIN_RSA_KEY_SIZE_BITS = 2048
USER_AGENT = "Flagsmith"

DESCRIBE_EVENTS_TABLE_QUERY = "DESCRIBE TABLE events"
WAREHOUSE_PROBE_QUERY = "SELECT environment_key FROM events LIMIT 1"

EVENTS_TABLE_COLUMN_TYPES = {
    "ENVIRONMENT_KEY": "VARCHAR",
    "EVENT": "VARCHAR",
    "FEATURE_NAME": "VARCHAR",
    "TIMESTAMP": "TIMESTAMP_NTZ",
    "COLLECTED_AT": "TIMESTAMP_NTZ",
    "IDENTIFIER": "VARCHAR",
    "VALUE": "VARCHAR",
    "TRAITS": "VARCHAR",
    "METADATA": "VARCHAR",
    "SDK_LANGUAGE": "VARCHAR",
    "SDK_VERSION": "VARCHAR",
}

ACCOUNT_NOT_FOUND_DETAIL = "Snowflake account not found."
ROLE_NOT_GRANTED_DETAIL = "The role does not exist or is not granted to the user."
WAREHOUSE_UNUSABLE_DETAIL = "Warehouse not found, or the role cannot use it."

_ERROR_CODE_DETAILS = {
    "390186": ROLE_NOT_GRANTED_DETAIL,
    "390189": ROLE_NOT_GRANTED_DETAIL,
    "002003": MISSING_EVENTS_TABLE_DETAIL,
    "000904": SCHEMA_MISMATCH_DETAIL,
    "391920": WAREHOUSE_UNUSABLE_DETAIL,
    "003001": PERMISSION_DENIED_DETAIL,
}


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
    "object": str,
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


def account_host(account_identifier: str) -> str:
    return f"{account_identifier.lower().replace('_', '-')}{HOST_SUFFIX}"


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
        self._base_url = f"https://{account_host(config['account_identifier'])}"
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
            if not isinstance(error, Mapping):
                error = {}
            raise SnowflakeRequestError(
                response.status_code, error.get("code"), error.get("sqlState")
            )
        return response

    def _poll_until_finished(self, response: requests.Response) -> requests.Response:
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
            if self._remaining() <= 0:
                continue
            try:
                response = self._request(
                    "GET",
                    f"/api/v2/statements/{statement_handle}",
                    read_timeout=max(self._remaining(), 1),
                )
            except (requests.Timeout, requests.ConnectionError):
                continue
            except SnowflakeRequestError as exc:
                if exc.status_code == 429:
                    continue
                raise
        return response

    def run(
        self,
        statement: str,
        params: Mapping[str, object],
        *,
        use_cached_result: bool = True,
    ) -> QueryResult:
        positional_statement, bindings = _rewrite_to_positional_bindings(
            statement, params
        )
        remaining_seconds = self._remaining()
        if remaining_seconds <= 0:
            raise SnowflakeTimeout()
        statement_timeout_seconds = max(
            math.ceil(remaining_seconds), MIN_STATEMENT_TIMEOUT_SECONDS
        )
        parameters = {"timezone": "UTC"}
        if not use_cached_result:
            parameters["use_cached_result"] = "false"
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
                    "parameters": parameters,
                },
            )
            response = self._poll_until_finished(response)
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
    if is_disallowed_host(account_host(config["account_identifier"])):
        raise DeliveryConfigError(
            "Host must not target internal or private network addresses."
        )
    with requests.Session() as http:
        yield _Session(http, config, credentials, time.monotonic() + budget_seconds)


def describe_snowflake_error(error: Exception) -> str:
    if isinstance(error, DeliveryConfigError):
        return str(error)
    if isinstance(error, SnowflakeAuthError):
        return "Authentication failed."
    if isinstance(error, SnowflakeTimeout):
        return QUERY_TIMEOUT_DETAIL
    if isinstance(error, EventsTableSchemaMismatchError):
        return SCHEMA_MISMATCH_DETAIL
    if isinstance(error, (requests.ConnectionError, requests.Timeout)):
        return "Could not connect to the host."
    if isinstance(error, SnowflakeRequestError):
        if error.status_code == 404 and error.error_code is None:
            return ACCOUNT_NOT_FOUND_DETAIL
        return _ERROR_CODE_DETAILS.get(
            error.error_code or "", "The Snowflake account rejected the request."
        )
    return "Connection failed."


def check_events_table(session: _Session) -> None:
    """Raise if the events table's columns don't match the setup SQL."""
    result = session.run(DESCRIBE_EVENTS_TABLE_QUERY, {})
    name_index = result.columns.index("name")
    type_index = result.columns.index("type")
    column_types = {
        row[name_index]: str(row[type_index]).split("(", 1)[0] for row in result.rows
    }
    if any(
        column_types.get(column) != column_type
        for column, column_type in EVENTS_TABLE_COLUMN_TYPES.items()
    ):
        raise EventsTableSchemaMismatchError()


def _normalise_account_identifier(account_identifier: str) -> str:
    host = account_identifier.strip().lower().split("://", 1)[-1]
    host = host.split("/", 1)[0].split("?", 1)[0]
    return host.removesuffix(HOST_SUFFIX).upper()


def _validate_account_identifier(account_identifier: object) -> None:
    if not account_identifier or not isinstance(account_identifier, str):
        raise serializers.ValidationError(
            {"config": {"account_identifier": "This field is required."}}
        )
    if not _ORGANISATION_ACCOUNT_IDENTIFIER.fullmatch(account_identifier):
        raise serializers.ValidationError(
            {
                "config": {
                    "account_identifier": (
                        "Enter the account identifier in the ORGNAME-ACCOUNTNAME form."
                    )
                }
            }
        )
    if is_disallowed_host(account_host(account_identifier)):
        raise serializers.ValidationError(
            {
                "config": {
                    "account_identifier": (
                        "Host must not target internal or private network addresses."
                    )
                }
            }
        )


def _private_key_error(message: str) -> serializers.ValidationError:
    return serializers.ValidationError({"credentials": {"private_key": message}})


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
        merged: dict[str, Any] = {**SNOWFLAKE_DEFAULTS, **(stored or {}), **config}
        if isinstance(merged["account_identifier"], str):
            merged["account_identifier"] = _normalise_account_identifier(
                merged["account_identifier"]
            )
        _validate_account_identifier(merged["account_identifier"])
        for key in ("warehouse", "database", "schema", "role", "user"):
            value = merged[key]
            if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
                raise serializers.ValidationError(
                    {"config": {key: "Enter a valid identifier."}}
                )
            merged[key] = value.upper()
        return typing.cast(SnowflakeConfig, merged)

    def validate_credentials(self, credentials: dict[str, Any]) -> SnowflakeCredentials:
        if not isinstance(credentials, dict):
            raise serializers.ValidationError({"credentials": "Must be an object."})
        private_key = credentials.get("private_key")
        if not private_key or not isinstance(private_key, str):
            raise _private_key_error("This field is required.")
        private_key = private_key.strip()
        try:
            loaded_key = serialization.load_pem_private_key(
                private_key.encode(), password=None
            )
        except (ValueError, TypeError, UnsupportedAlgorithm) as exc:
            raise _private_key_error(
                "Enter an unencrypted private key in PEM format."
            ) from exc
        if not isinstance(loaded_key, rsa.RSAPrivateKey):
            raise _private_key_error("Enter an RSA private key.")
        if loaded_key.key_size < MIN_RSA_KEY_SIZE_BITS:
            raise _private_key_error(
                f"Enter an RSA private key of at least {MIN_RSA_KEY_SIZE_BITS} bits."
            )
        return {"private_key": private_key}

    def verify(self, connection: WarehouseConnection) -> None:
        with snowflake_session(
            connection, budget_seconds=VERIFY_TIMEOUT_SECONDS
        ) as session:
            check_events_table(session)
            session.run(WAREHOUSE_PROBE_QUERY, {}, use_cached_result=False)

    def describe_error(self, error: Exception) -> str:
        return describe_snowflake_error(error)

    def get_event_names(
        self,
        connection: WarehouseConnection,
        environment_key: str,
    ) -> WarehouseEventNames | None:
        cache_key = customer_cache_key("event_names", connection)
        cached = cache.get(cache_key)
        if isinstance(cached, WarehouseEventNames):
            return cached
        if cached == CUSTOMER_EVENT_UNAVAILABLE:
            return None
        try:
            with snowflake_session(
                connection, budget_seconds=EVENT_NAMES_TIMEOUT_SECONDS
            ) as session:
                event_names = build_event_names(
                    session.run(
                        event_names_query(SNOWFLAKE_DIALECT),
                        event_names_query_params(environment_key),
                    )[0]
                )
        except Exception:
            cache.set(
                cache_key,
                CUSTOMER_EVENT_UNAVAILABLE,
                CUSTOMER_EVENT_NAMES_FAILURE_CACHE_SECONDS,
            )
            logger.warning(
                "connection.event_names_failed",
                environment__id=connection.environment_id,
                exc_info=True,
            )
            return None
        cache_warehouse_read_unless_empty(
            cache_key, event_names, EVENT_NAMES_CACHE_SECONDS
        )
        return event_names

    def get_event_stats(
        self,
        connection: WarehouseConnection,
        environment_key: str,
    ) -> WarehouseEventStats | None:
        cache_key = customer_cache_key("event_stats", connection)
        cached = cache.get(cache_key)
        if isinstance(cached, WarehouseEventStats):
            return cached
        if cached == CUSTOMER_EVENT_UNAVAILABLE:
            return None
        try:
            with snowflake_session(
                connection, budget_seconds=VERIFY_TIMEOUT_SECONDS
            ) as session:
                stats = build_event_stats(
                    session.run(
                        event_stats_query(SNOWFLAKE_DIALECT),
                        {"environment_key": environment_key},
                    )[0]
                )
        except Exception:
            cache.set(
                cache_key,
                CUSTOMER_EVENT_UNAVAILABLE,
                CUSTOMER_EVENT_STATS_CACHE_SECONDS,
            )
            logger.warning(
                "connection.event_stats_failed",
                environment__id=connection.environment_id,
                exc_info=True,
            )
            return None
        cache_warehouse_read_unless_empty(
            cache_key, stats, CUSTOMER_EVENT_STATS_CACHE_SECONDS
        )
        return stats

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
        with snowflake_session(
            connection, budget_seconds=BACKGROUND_QUERY_TIMEOUT_SECONDS
        ) as session:
            return read_exposure_buckets(
                session.run,
                SNOWFLAKE_DIALECT,
                environment_key=environment_key,
                feature_name=feature_name,
                window_start=window_start,
                window_end=window_end,
                granularity=granularity,
            )

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
        with snowflake_session(
            connection, budget_seconds=BACKGROUND_QUERY_TIMEOUT_SECONDS
        ) as session:
            return read_results_aggregates(
                session.run,
                SNOWFLAKE_DIALECT,
                environment_key=environment_key,
                feature_name=feature_name,
                window_start=window_start,
                window_end=window_end,
                specs=specs,
                granularity=granularity,
            )
