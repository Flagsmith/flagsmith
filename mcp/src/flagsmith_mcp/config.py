import os
from typing import Literal, get_args

Transport = Literal["http", "stdio"]
TRANSPORTS: tuple[Transport, ...] = get_args(Transport)

# TODO: consume a version-controlled schema — https://github.com/Flagsmith/flagsmith/issues/7669
OPENAPI_SPEC_URL = "https://api.flagsmith.com/api/v1/swagger.json"

DEFAULT_API_URL = "https://api.flagsmith.com"
DEFAULT_TRANSPORT: Transport = "http"


def get_api_url() -> str:
    return os.environ.get("FLAGSMITH_API_URL", DEFAULT_API_URL)


def get_transport() -> Transport:
    transport = os.environ.get("TRANSPORT", DEFAULT_TRANSPORT)
    for candidate in TRANSPORTS:
        if transport == candidate:
            return candidate
    raise ValueError(
        f"Unsupported TRANSPORT {transport!r}; expected one of {', '.join(TRANSPORTS)}"
    )
