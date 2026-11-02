"""The SDK event contract, mirrored from the ingestion server so SDKs send
events here unchanged. Limits are named after its constants:
https://github.com/Flagsmith/ingestion-server/blob/main/src/routes/ingest.rs"""

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from experimentation.constants import EXPOSURE_EVENT_NAME
from experimentation.models import SDKExperimentationEvent
from experimentation.types import RejectedSDKEvent

# 2020-01-01T00:00:00Z.
MIN_TIMESTAMP_MS = 1_577_836_800_000
MAX_FUTURE_SKEW_HOURS = 24
MAX_EVENT_AGE_DAYS = 10

MAX_EVENT_NAME_CHARS = 256
MAX_FEATURE_NAME_CHARS = 2000
MAX_IDENTIFIER_CHARS = 2000
MAX_TRAIT_KEY_CHARS = 200
MAX_TRAIT_STRING_VALUE_CHARS = 2000

MAX_VALUE_BYTES = 128 * 1024
MAX_TRAITS_BYTES = 32 * 1024
MAX_METADATA_BYTES = 8 * 1024

MAX_SDK_FIELD_CHARS = 100

EMPTY_BATCH_ERROR = "events must be non-empty"

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_SDK_USER_AGENT_PATTERN = re.compile(r"flagsmith-(.*)-sdk", re.DOTALL)


def partition_sdk_events(
    events: list[object],
    now: datetime,
) -> tuple[list[dict[str, Any]], list[RejectedSDKEvent]]:
    """Split a batch into storable events and per-event rejections, so one
    invalid event never blocks its neighbours."""
    now_ms = (now - _EPOCH) // timedelta(milliseconds=1)
    valid: list[dict[str, Any]] = []
    rejected: list[RejectedSDKEvent] = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            rejected.append(
                {"index": index, "error": f"events[{index}] must be an object"}
            )
        elif error := _validate_sdk_event(event, now_ms):
            rejected.append({"index": index, "error": f"events[{index}].{error}"})
        else:
            valid.append(event)
    return valid, rejected


def parse_sdk_user_agent(header: str | None) -> tuple[str, str]:
    """Return the SDK language and version from a `Flagsmith-SDK-User-Agent`
    header such as `flagsmith-js-sdk/11.0.0`."""
    if header is None:
        return "unknown", "unknown"
    sdk_part, separator, version = header.partition("/")
    match = _SDK_USER_AGENT_PATTERN.fullmatch(sdk_part)
    language = match[1] if match else "unknown"
    return (
        language[:MAX_SDK_FIELD_CHARS],
        (version if separator else "unknown")[:MAX_SDK_FIELD_CHARS],
    )


def build_sdk_experimentation_event(
    event: dict[str, Any],
    *,
    environment_key: str,
    collected_at: datetime,
    sdk_language: str,
    sdk_version: str,
) -> SDKExperimentationEvent:
    """Map a valid event to its row: JSON values other than strings are stored
    as compact JSON, and a missing identifier as an empty string."""
    return SDKExperimentationEvent(
        environment_key=environment_key,
        event=_as_column_text(event["event"]) or "",
        feature_name=_as_column_text(event.get("feature_name")),
        timestamp=_EPOCH + timedelta(milliseconds=event["timestamp"]),
        collected_at=collected_at,
        identifier=_as_column_text(event.get("identifier")) or "",
        value=_as_column_text(event.get("value")),
        traits=_as_column_text(event.get("traits")),
        metadata=_as_column_text(event.get("metadata")),
        sdk_language=sdk_language,
        sdk_version=sdk_version,
    )


def _validate_sdk_event(event: dict[str, Any], now_ms: int) -> str | None:
    """Return the first rule the event breaks, in the ingestion server's order."""
    name = event.get("event", "")
    feature_name = event.get("feature_name")
    return (
        _validate_event_name(name)
        or (
            f"feature_name is required for {EXPOSURE_EVENT_NAME} events"
            if name == EXPOSURE_EVENT_NAME and feature_name is None
            else None
        )
        or _validate_optional_string(
            "feature_name", feature_name, MAX_FEATURE_NAME_CHARS
        )
        or _validate_optional_string(
            "identifier", event.get("identifier"), MAX_IDENTIFIER_CHARS
        )
        or _validate_timestamp(event.get("timestamp", 0), now_ms)
        or _validate_json_fields(event)
    )


def _validate_event_name(name: object) -> str | None:
    if not isinstance(name, str):
        return "event must be a string"
    if not name.strip():
        return "event must be non-empty"
    if len(name) > MAX_EVENT_NAME_CHARS:
        return f"event must be at most {MAX_EVENT_NAME_CHARS} characters"
    if name.startswith("$") and name != EXPOSURE_EVENT_NAME:
        return f'event "{name}" uses the reserved `$` prefix but is not a known system event'
    return None


def _validate_optional_string(field: str, value: object, max_chars: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return f"{field} must be a string"
    if len(value) > max_chars:
        return f"{field} must be at most {max_chars} characters"
    return None


def _validate_timestamp(timestamp: object, now_ms: int) -> str | None:
    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        return "timestamp must be an integer"
    if timestamp <= MIN_TIMESTAMP_MS:
        return "timestamp must be an epoch-millis value after 2020-01-01"
    if timestamp > now_ms + MAX_FUTURE_SKEW_HOURS * 3_600_000:
        return f"timestamp must not be more than {MAX_FUTURE_SKEW_HOURS}h in the future"
    if timestamp < now_ms - MAX_EVENT_AGE_DAYS * 86_400_000:
        return f"timestamp must not be more than {MAX_EVENT_AGE_DAYS} days in the past"
    return None


def _validate_json_fields(event: dict[str, Any]) -> str | None:
    if _json_size(event.get("value")) > MAX_VALUE_BYTES:
        return f"value must serialize to at most {MAX_VALUE_BYTES} bytes"
    if (traits := event.get("traits")) is not None:
        if _json_size(traits) > MAX_TRAITS_BYTES:
            return f"traits must serialize to at most {MAX_TRAITS_BYTES} bytes"
        if not isinstance(traits, dict):
            return "traits must be a JSON object"
        for key, value in traits.items():
            if len(key) > MAX_TRAIT_KEY_CHARS:
                return f"trait keys must be at most {MAX_TRAIT_KEY_CHARS} characters"
            if isinstance(value, str) and len(value) > MAX_TRAIT_STRING_VALUE_CHARS:
                return f'traits["{key}"] string values must be at most {MAX_TRAIT_STRING_VALUE_CHARS} characters'
    metadata = event.get("metadata")
    if metadata is not None and _json_size(metadata) > MAX_METADATA_BYTES:
        return f"metadata must serialize to at most {MAX_METADATA_BYTES} bytes"
    return None


def _json_size(value: object) -> int:
    """Serialised size in UTF-8 bytes, as the ingestion server measures it."""
    return len(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode(
            errors="surrogatepass"
        )
    )


def _as_column_text(value: object) -> str | None:
    if value is None:
        return None
    text = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))
    # PostgreSQL text cannot hold NUL.
    return text.replace("\x00", "")
