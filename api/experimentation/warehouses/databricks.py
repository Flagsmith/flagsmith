import math
import re
import time
import typing
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, suppress
from datetime import datetime, timezone
from typing import Any, TypeVar

import requests
import structlog
from django.core.cache import cache
from rest_framework import serializers

from core.network import is_internal_address
from experimentation.dataclasses import (
    ExposureBucket,
    ResultsAggregates,
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.types import (
    DATABRICKS_DEFAULTS,
    DatabricksConfig,
    DatabricksCredentials,
)
from experimentation.warehouses.cache import (
    CUSTOMER_EVENT_UNAVAILABLE,
    customer_cache_key,
)
from experimentation.warehouses.constants import (
    BACKGROUND_QUERY_TIMEOUT_SECONDS,
    CUSTOMER_EVENT_NAMES_FAILURE_CACHE_SECONDS,
    CUSTOMER_EVENT_STATS_CACHE_SECONDS,
    EVENT_NAMES_CACHE_SECONDS,
    EVENT_NAMES_TIMEOUT_SECONDS,
    MISSING_EVENTS_TABLE_DETAIL,
    VERIFY_TIMEOUT_SECONDS,
)
from experimentation.warehouses.dialect import DATABRICKS_DIALECT
from experimentation.warehouses.exceptions import DeliveryConfigError
from experimentation.warehouses.queries import (
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

T = TypeVar("T")

HOST_SUFFIXES = (".cloud.databricks.com", ".azuredatabricks.net", ".gcp.databricks.com")
_HOSTNAME = re.compile(r"(?!-)[a-z0-9-]+(?<!-)(\.(?!-)[a-z0-9-]+(?<!-))+")
_WAREHOUSE_ID = re.compile(r"[A-Za-z0-9]+")
_IDENTIFIER = re.compile(r"[A-Za-z0-9_]+")
_WORKSPACE_ID = re.compile(r"[0-9]+")
_REGION = re.compile(r"[a-z0-9-]+")
_HOST_WORKSPACE_ID = re.compile(r"[?&]o=([0-9]+)")
_ERROR_CLASS = re.compile(r"\[([A-Z_]+)\]")
_SCOPE_NOT_ASSIGNED = re.compile(r"scopes? .* not assigned", re.IGNORECASE)
ORG_ID_HEADER = "x-databricks-org-id"

CONNECT_TIMEOUT_SECONDS = 5
POLL_INTERVAL_SECONDS = 1
MAX_WAIT_TIMEOUT_SECONDS = 30
MIN_WAIT_TIMEOUT_SECONDS = 5
_TERMINAL_STATES = {"SUCCEEDED", "FAILED", "CANCELED", "CLOSED"}

VERIFY_QUERY = "SELECT 1 FROM events LIMIT 0"

WAREHOUSE_STARTING_DETAIL = (
    "The SQL warehouse is starting. Test the connection again in a few minutes."
)
SECRET_SCOPE_DETAIL = (
    "The service principal secret must allow the sql scope. "
    "Generate a new secret with the sql scope."
)


class DatabricksAuthError(Exception):
    pass


class DatabricksSecretScopeError(Exception):
    pass


class DatabricksWorkspaceMismatch(Exception):
    pass


class DatabricksWarehouseStarting(Exception):
    pass


class DatabricksTimeout(Exception):
    pass


class DatabricksRequestError(Exception):
    def __init__(
        self,
        status_code: int | None,
        error_class: str | None,
        description: str | None = None,
    ) -> None:
        super().__init__(f"Databricks request failed: {status_code} {error_class}")
        self.status_code = status_code
        self.error_class = error_class
        self.description = description


def _error_class(error: dict[str, Any]) -> str | None:
    match = _ERROR_CLASS.search(str(error.get("message", "")))
    return match.group(1) if match else error.get("error_code")


def _parameter(name: str, value: object) -> dict[str, str]:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError(f"Parameter {name} must be timezone-aware.")
        return {
            "name": name,
            "value": value.astimezone(timezone.utc).isoformat(),
            "type": "TIMESTAMP",
        }
    if isinstance(value, bool):
        raise TypeError(f"Unsupported parameter type for {name}: bool")
    if isinstance(value, int):
        return {"name": name, "value": str(value), "type": "INT"}
    if isinstance(value, str):
        return {"name": name, "value": value, "type": "STRING"}
    raise TypeError(f"Unsupported parameter type for {name}: {type(value).__name__}")


def _parameters(statement: str, params: Mapping[str, object]) -> list[dict[str, str]]:
    return [
        _parameter(name, value)
        for name, value in params.items()
        if re.search(rf":{re.escape(name)}(?![A-Za-z0-9_])", statement)
    ]


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Databricks returned a TIMESTAMP without an offset.")
    return parsed.astimezone(timezone.utc)


_CONVERTERS: dict[str, Callable[[str], object]] = {
    "BIGINT": int,
    "INT": int,
    "LONG": int,
    "SHORT": int,
    "DOUBLE": float,
    "FLOAT": float,
    "DECIMAL": float,
    "BOOLEAN": lambda value: value == "true",
    "TIMESTAMP": _parse_timestamp,
    "STRING": str,
}


def _convert_rows(
    payload: dict[str, Any],
) -> tuple[list[list[object]], list[str]]:
    result = payload.get("result") or {}
    if result.get("next_chunk_index") is not None:
        raise DatabricksRequestError(None, "MULTI_CHUNK_RESULT")
    columns = payload["manifest"]["schema"]["columns"]
    converters = [_CONVERTERS[column["type_name"]] for column in columns]
    rows = [
        [
            None if value is None else convert(value)
            for convert, value in zip(converters, row)
        ]
        for row in result.get("data_array") or []
    ]
    return rows, [column["name"] for column in columns]


class _Session:
    def __init__(
        self,
        http: requests.Session,
        config: DatabricksConfig,
        credentials: DatabricksCredentials,
        deadline: float,
    ) -> None:
        self._http = http
        self._config = config
        self._base_url = f"https://{config['host']}"
        self._deadline = deadline
        self.org_id: str | None = None
        self._headers = {"Authorization": f"Bearer {self._fetch_token(credentials)}"}

    def check_workspace(self) -> None:
        if self.org_id and self.org_id != self._config["workspace_id"]:
            raise DatabricksWorkspaceMismatch()

    def _remaining(self) -> float:
        return self._deadline - time.monotonic()

    def _request(
        self, method: str, path: str, *, read_timeout: float, **kwargs: Any
    ) -> dict[str, Any]:
        response = self._http.request(
            method,
            f"{self._base_url}{path}",
            timeout=(CONNECT_TIMEOUT_SECONDS, read_timeout),
            allow_redirects=False,
            **kwargs,
        )
        if response.status_code != 200:
            try:
                error = response.json()
            except ValueError:
                error = {}
            raise DatabricksRequestError(
                response.status_code,
                _error_class(error),
                error.get("error_description"),
            )
        self.org_id = response.headers.get(ORG_ID_HEADER) or self.org_id
        payload: dict[str, Any] = response.json()
        return payload

    def _fetch_token(self, credentials: DatabricksCredentials) -> str:
        try:
            payload = self._request(
                "POST",
                "/oidc/v1/token",
                read_timeout=max(self._remaining(), 1),
                auth=(credentials["client_id"], credentials["client_secret"]),
                data={"grant_type": "client_credentials", "scope": "sql"},
            )
        except DatabricksRequestError as exc:
            if _SCOPE_NOT_ASSIGNED.search(exc.description or ""):
                raise DatabricksSecretScopeError() from exc
            if exc.status_code in (400, 401):
                raise DatabricksAuthError() from exc
            raise
        token: str = payload["access_token"]
        return token

    def run(
        self, statement: str, params: Mapping[str, object]
    ) -> tuple[list[list[object]], list[str]]:
        wait = min(math.ceil(self._remaining()), MAX_WAIT_TIMEOUT_SECONDS)
        if wait < MIN_WAIT_TIMEOUT_SECONDS:
            wait = 0
        payload = self._request(
            "POST",
            "/api/2.0/sql/statements",
            read_timeout=wait + CONNECT_TIMEOUT_SECONDS,
            headers=self._headers,
            json={
                "warehouse_id": self._config["warehouse_id"],
                "catalog": self._config["catalog"],
                "schema": self._config["schema"],
                "statement": statement,
                "parameters": _parameters(statement, params),
                "wait_timeout": f"{wait}s",
                "on_wait_timeout": "CONTINUE",
                "disposition": "INLINE",
                "format": "JSON_ARRAY",
            },
        )
        statement_id = payload["statement_id"]
        state = payload["status"]["state"]
        while state not in _TERMINAL_STATES:
            if self._remaining() <= 0:
                with suppress(requests.RequestException, DatabricksRequestError):
                    self._request(
                        "POST",
                        f"/api/2.0/sql/statements/{statement_id}/cancel",
                        read_timeout=CONNECT_TIMEOUT_SECONDS,
                        headers=self._headers,
                    )
                if state == "PENDING":
                    raise DatabricksWarehouseStarting()
                raise DatabricksTimeout()
            time.sleep(POLL_INTERVAL_SECONDS)
            try:
                payload = self._request(
                    "GET",
                    f"/api/2.0/sql/statements/{statement_id}",
                    read_timeout=max(self._remaining(), 1),
                    headers=self._headers,
                )
            except requests.Timeout:
                continue
            state = payload["status"]["state"]
        if state != "SUCCEEDED":
            raise DatabricksRequestError(
                None, _error_class(payload["status"].get("error") or {})
            )
        return _convert_rows(payload)


@contextmanager
def databricks_session(
    connection: "WarehouseConnection", *, budget_seconds: float
) -> Iterator[_Session]:
    """Yield a session holding one token, for every statement of one operation."""
    config = typing.cast(DatabricksConfig, connection.config or {})
    credentials = typing.cast(DatabricksCredentials, connection.credentials or {})
    if not (
        DatabricksConfig.__required_keys__ <= config.keys()
        and DatabricksCredentials.__required_keys__ <= credentials.keys()
    ):
        raise DeliveryConfigError("Stored connection details are incomplete.")
    if is_internal_address(config["host"], include_shared=True):
        raise DeliveryConfigError(
            "Host must not target internal or private network addresses."
        )
    with requests.Session() as http:
        yield _Session(http, config, credentials, time.monotonic() + budget_seconds)


def _describe_request_error(error: DatabricksRequestError) -> str:
    if error.status_code == 401 or (
        error.status_code == 403 and error.error_class is None
    ):
        return "Authentication failed."
    if error.error_class == "TABLE_OR_VIEW_NOT_FOUND":
        return MISSING_EVENTS_TABLE_DETAIL
    if error.error_class in (
        "SCHEMA_NOT_FOUND",
        "CATALOG_NOT_FOUND",
        "NO_SUCH_CATALOG_EXCEPTION",
    ):
        return "Database does not exist."
    if error.status_code == 404 or error.error_class == "RESOURCE_DOES_NOT_EXIST":
        return "SQL warehouse not found."
    return "The Databricks workspace rejected the request."


def describe_databricks_error(error: Exception) -> str:
    if isinstance(error, DeliveryConfigError):
        return str(error)
    if isinstance(error, DatabricksAuthError):
        return "Authentication failed."
    if isinstance(error, DatabricksSecretScopeError):
        return SECRET_SCOPE_DETAIL
    if isinstance(error, DatabricksWorkspaceMismatch):
        return "The workspace ID does not match this workspace."
    if isinstance(error, DatabricksWarehouseStarting):
        return WAREHOUSE_STARTING_DETAIL
    if isinstance(
        error, (requests.ConnectionError, requests.Timeout, DatabricksTimeout)
    ):
        return "Could not connect to the host."
    if isinstance(error, DatabricksRequestError):
        return _describe_request_error(error)
    return "Connection failed."


def _workspace_id_from_host(host: str) -> str | None:
    match = _HOST_WORKSPACE_ID.search(host)
    return match.group(1) if match else None


def _normalise_host(host: str) -> str:
    host = host.strip().lower().split("://", 1)[-1]
    return host.split("/", 1)[0].split("?", 1)[0]


def _normalise_warehouse_id(warehouse_id: str) -> str:
    return warehouse_id.strip().rstrip("/").rsplit("/", 1)[-1]


_NORMALISERS: dict[str, Callable[[str], str]] = {
    "host": _normalise_host,
    "workspace_id": str.strip,
    "region": lambda region: region.strip().lower(),
    "warehouse_id": _normalise_warehouse_id,
}


def _normalise_config(config: dict[str, Any], merged: dict[str, Any]) -> None:
    host = merged["host"]
    if (
        isinstance(host, str)
        and not config.get("workspace_id")
        and (workspace_id := _workspace_id_from_host(host))
    ):
        merged["workspace_id"] = workspace_id
    for key, normalise in _NORMALISERS.items():
        if isinstance(merged[key], str):
            merged[key] = normalise(merged[key])


def _validate_host(host: object) -> None:
    if not host or not isinstance(host, str):
        raise serializers.ValidationError(
            {"config": {"host": "This field is required."}}
        )
    if not _HOSTNAME.fullmatch(host) or not host.endswith(HOST_SUFFIXES):
        raise serializers.ValidationError(
            {"config": {"host": "Enter a Databricks workspace hostname."}}
        )
    if is_internal_address(host, include_shared=True):
        raise serializers.ValidationError(
            {
                "config": {
                    "host": (
                        "Host must not target internal or private network addresses."
                    )
                }
            }
        )


class DatabricksWarehouse:
    def validate_config(
        self,
        config: dict[str, Any],
        *,
        stored: dict[str, Any] | None = None,
    ) -> DatabricksConfig:
        if not isinstance(config, dict):
            raise serializers.ValidationError({"config": "Must be an object."})
        if unknown_keys := set(config) - set(DATABRICKS_DEFAULTS):
            raise serializers.ValidationError(
                {"config": {key: "Unknown field." for key in sorted(unknown_keys)}}
            )
        merged: dict[str, Any] = {**DATABRICKS_DEFAULTS, **(stored or {}), **config}
        _normalise_config(config, merged)
        _validate_host(merged["host"])
        for key, pattern, message in (
            ("workspace_id", _WORKSPACE_ID, "Enter the numeric workspace ID."),
            ("region", _REGION, "Enter the workspace region, e.g. us-east-1."),
            ("warehouse_id", _WAREHOUSE_ID, "Enter a valid identifier."),
            ("catalog", _IDENTIFIER, "Enter a valid identifier."),
            ("schema", _IDENTIFIER, "Enter a valid identifier."),
        ):
            value = merged[key]
            if not isinstance(value, str) or not pattern.fullmatch(value):
                raise serializers.ValidationError({"config": {key: message}})
        return typing.cast(DatabricksConfig, merged)

    def validate_credentials(
        self, credentials: dict[str, Any]
    ) -> DatabricksCredentials:
        if not isinstance(credentials, dict):
            raise serializers.ValidationError({"credentials": "Must be an object."})
        for key in ("client_id", "client_secret"):
            value = credentials.get(key)
            if not value or not isinstance(value, str):
                raise serializers.ValidationError(
                    {"credentials": {key: "This field is required."}}
                )
        return {
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"],
        }

    def verify(self, connection: "WarehouseConnection") -> None:
        with databricks_session(
            connection, budget_seconds=VERIFY_TIMEOUT_SECONDS
        ) as session:
            session.check_workspace()
            session.run(VERIFY_QUERY, {})

    def describe_error(self, error: Exception) -> str:
        return describe_databricks_error(error)

    def _cached_read(
        self,
        connection: "WarehouseConnection",
        *,
        kind: str,
        result_type: type[T],
        success_seconds: int,
        failure_seconds: int,
        budget_seconds: float,
        read: Callable[[_Session], T],
    ) -> T | None:
        cache_key = customer_cache_key(kind, connection)
        cached = cache.get(cache_key)
        if isinstance(cached, result_type):
            return cached
        if cached == CUSTOMER_EVENT_UNAVAILABLE:
            return None
        try:
            with databricks_session(
                connection, budget_seconds=budget_seconds
            ) as session:
                result = read(session)
        except Exception:
            cache.set(cache_key, CUSTOMER_EVENT_UNAVAILABLE, failure_seconds)
            logger.warning(
                f"connection.{kind}_failed",
                environment__id=connection.environment_id,
                exc_info=True,
            )
            return None
        cache.set(cache_key, result, success_seconds)
        return result

    def get_event_names(
        self,
        connection: "WarehouseConnection",
        environment_key: str,
    ) -> WarehouseEventNames | None:
        return self._cached_read(
            connection,
            kind="event_names",
            result_type=WarehouseEventNames,
            success_seconds=EVENT_NAMES_CACHE_SECONDS,
            failure_seconds=CUSTOMER_EVENT_NAMES_FAILURE_CACHE_SECONDS,
            budget_seconds=EVENT_NAMES_TIMEOUT_SECONDS,
            read=lambda session: build_event_names(
                session.run(
                    event_names_query(DATABRICKS_DIALECT),
                    event_names_query_params(environment_key),
                )[0]
            ),
        )

    def get_event_stats(
        self,
        connection: "WarehouseConnection",
        environment_key: str,
    ) -> WarehouseEventStats | None:
        return self._cached_read(
            connection,
            kind="event_stats",
            result_type=WarehouseEventStats,
            success_seconds=CUSTOMER_EVENT_STATS_CACHE_SECONDS,
            failure_seconds=CUSTOMER_EVENT_STATS_CACHE_SECONDS,
            budget_seconds=VERIFY_TIMEOUT_SECONDS,
            read=lambda session: build_event_stats(
                session.run(
                    event_stats_query(DATABRICKS_DIALECT),
                    {"environment_key": environment_key},
                )[0]
            ),
        )

    def get_exposure_buckets(
        self,
        connection: "WarehouseConnection",
        *,
        environment_key: str,
        feature_name: str,
        window_start: datetime,
        window_end: datetime,
        granularity: "ExposureGranularity",
    ) -> list[ExposureBucket]:
        with databricks_session(
            connection, budget_seconds=BACKGROUND_QUERY_TIMEOUT_SECONDS
        ) as session:
            return read_exposure_buckets(
                session.run,
                DATABRICKS_DIALECT,
                environment_key=environment_key,
                feature_name=feature_name,
                window_start=window_start,
                window_end=window_end,
                granularity=granularity,
            )

    def get_results_aggregates(
        self,
        connection: "WarehouseConnection",
        *,
        environment_key: str,
        feature_name: str,
        window_start: datetime,
        window_end: datetime,
        specs: "Sequence[MetricSpec]",
        granularity: "ExposureGranularity",
    ) -> ResultsAggregates:
        with databricks_session(
            connection, budget_seconds=BACKGROUND_QUERY_TIMEOUT_SECONDS
        ) as session:
            return read_results_aggregates(
                session.run,
                DATABRICKS_DIALECT,
                environment_key=environment_key,
                feature_name=feature_name,
                window_start=window_start,
                window_end=window_end,
                specs=specs,
                granularity=granularity,
            )
