from dataclasses import dataclass


@dataclass
class SSEAccessLogs:
    generated_at: str  # ISO 8601
    api_key: str
