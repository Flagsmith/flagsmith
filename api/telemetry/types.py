from typing import TypedDict


class ResolvedTelemetryAttributes(TypedDict, total=False):
    """Telemetry-relevant attributes from objects an API request acts on"""

    organisation__id: int
    project__id: int
    feature__id: int
    environment__id: int
    environment__key: str
