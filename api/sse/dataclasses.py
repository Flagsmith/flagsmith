from dataclasses import dataclass


@dataclass(eq=True)
class SSEAccessLogs:
    generated_at: str  # ISO 8601
    api_key: str
