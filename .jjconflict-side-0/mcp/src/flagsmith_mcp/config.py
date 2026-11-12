from typing import Literal

from pydantic import Field, HttpUrl, model_validator
from pydantic_settings import BaseSettings

Transport = Literal["http", "stdio"]


class Settings(BaseSettings):
    model_config = {"use_attribute_docstrings": True}

    environment: str | None = Field(
        default=None,
    )
    """Deployment environment."""
    flagsmith_api_url: HttpUrl = Field(
        default=HttpUrl("https://api.flagsmith.com"),
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
    metrics_port: int | None = Field(
        default=None,
    )
    """Serve Prometheus metrics on this port. Disabled when unset."""
    log_level: str = Field(
        default="INFO",
    )
    """Log level for application loggers."""
    log_format: Literal["generic", "json"] = Field(
        default="generic",
    )
    """Log output format."""
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None,
    )
    """OTLP endpoint to export logs and traces to. Export is disabled when
    unset."""
    otel_service_name: str = Field(
        default="flagsmith-mcp",
    )
    """Service name reported to OpenTelemetry."""
    mcp_server_url: HttpUrl = Field(
        default=HttpUrl("http://127.0.0.1:8000"),
    )
    """Public base URL of this MCP server, advertised in OAuth protected-resource
    metadata. Override for HTTP deployments behind a proxy/public hostname."""
    sentry_dsn: HttpUrl | None = Field(
        default=None,
    )
    """Sentry DSN for error reporting. Error capture is disabled when unset."""

    @model_validator(mode="after")
    def validate_stdio_token(self) -> "Settings":
        # stdio has no inbound request to forward a credential from, so the
        # server must hold its own master API key.
        if self.transport == "stdio" and self.flagsmith_api_token is None:
            raise ValueError(
                "FLAGSMITH_API_TOKEN is required when TRANSPORT is 'stdio'"
            )
        return self
