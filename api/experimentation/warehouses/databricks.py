import math
import re
import time
import typing
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, suppress
from datetime import datetime, timezone
from typing import Any

import requests

from core.network import is_internal_address
from experimentation.types import DatabricksConfig, DatabricksCredentials
from experimentation.warehouses.constants import MISSING_EVENTS_TABLE_DETAIL
from experimentation.warehouses.exceptions import DeliveryConfigError

if typing.TYPE_CHECKING:
    from experimentation.models import WarehouseConnection

_ERROR_CLASS = re.compile(r"\[([A-Z_]+)\]")
_SCOPE_NOT_ASSIGNED = re.compile(r"scopes? .* not assigned", re.IGNORECASE)

CONNECT_TIMEOUT_SECONDS = 5
POLL_INTERVAL_SECONDS = 1
MAX_WAIT_TIMEOUT_SECONDS = 30
MIN_WAIT_TIMEOUT_SECONDS = 5
_TERMINAL_STATES = {"SUCCEEDED", "FAILED", "CANCELED", "CLOSED"}

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
        self._headers = {"Authorization": f"Bearer {self._fetch_token(credentials)}"}

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
    if isinstance(error, DatabricksWarehouseStarting):
        return WAREHOUSE_STARTING_DETAIL
    if isinstance(
        error, (requests.ConnectionError, requests.Timeout, DatabricksTimeout)
    ):
        return "Could not connect to the host."
    if isinstance(error, DatabricksRequestError):
        return _describe_request_error(error)
    return "Connection failed."
