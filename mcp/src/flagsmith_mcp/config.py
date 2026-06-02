from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings

Transport = Literal["http", "stdio"]

# TODO: consume a version-controlled schema — https://github.com/Flagsmith/flagsmith/issues/7669
OPENAPI_SPEC_URL = "https://api.flagsmith.com/api/v1/swagger.json"


class Settings(BaseSettings):
    model_config = {"use_attribute_docstrings": True}

    flagsmith_api_url: str = Field(
        default="https://api.flagsmith.com",
    )
    """Flagsmith API base URL."""
    flagsmith_api_token: str | None = Field(
        default=None,
    )
    """Flagsmith Master API Key. Required for stdio transport, optional for http transport (caller-supplied credential will be used instead)."""
    transport: Transport = Field(
        default="http",
    )
    """MCP transport to use."""
