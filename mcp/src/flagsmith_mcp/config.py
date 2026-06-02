from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

Transport = Literal["http", "stdio"]


class Settings(BaseSettings):
    model_config = {"use_attribute_docstrings": True}

    flagsmith_api_url: str = Field(
        default="https://api.flagsmith.com",
    )
    """Flagsmith API base URL."""
    flagsmith_api_token: str | None = Field(
        default=None,
    )
    """Flagsmith Master API Key. Required for stdio transport."""
    transport: Transport = Field(
        default="http",
    )
    """MCP transport to use."""

    @model_validator(mode="after")
    def validate_stdio_token(self) -> "Settings":
        # stdio has no inbound request to forward a credential from, so the
        # server must hold its own master API key.
        if self.transport == "stdio" and self.flagsmith_api_token is None:
            raise ValueError(
                "FLAGSMITH_API_TOKEN is required when TRANSPORT is 'stdio'"
            )
        return self
