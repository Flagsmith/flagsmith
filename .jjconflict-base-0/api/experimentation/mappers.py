import json
from datetime import datetime, timezone
from typing import Any

from experimentation.models import SDKExperimentationEvent


def map_sdk_event_to_sdk_experimentation_event(
    event: dict[str, Any],
    *,
    environment_key: str,
    collected_at: datetime,
    sdk_language: str,
    sdk_version: str,
) -> SDKExperimentationEvent:
    return SDKExperimentationEvent(
        environment_key=environment_key,
        event=event["event"],
        feature_name=event.get("feature_name"),
        timestamp=datetime.fromtimestamp(event["timestamp"] / 1000, tz=timezone.utc),
        collected_at=collected_at,
        identifier=event.get("identifier") or "",
        value=_as_json_column_text(event.get("value")),
        traits=_as_json_column_text(event.get("traits")),
        metadata=_as_json_column_text(event.get("metadata")),
        sdk_language=sdk_language,
        sdk_version=sdk_version,
    )


def _as_json_column_text(value: object) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
