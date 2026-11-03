"""Accepts the payload and limits of https://github.com/Flagsmith/ingestion-server/blob/main/src/routes/ingest.rs, with DRF-style error messages."""

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from django.core.validators import ProhibitNullCharactersValidator
from rest_framework import serializers
from rest_framework.validators import ProhibitSurrogateCharactersValidator

from environments.identities.constants import IDENTITY_IDENTIFIER_MAX_LENGTH
from environments.identities.traits.constants import (
    TRAIT_KEY_MAX_LENGTH,
    TRAIT_STRING_VALUE_MAX_LENGTH,
)
from experimentation.constants import EXPOSURE_EVENT_NAME
from experimentation.models import SDKExperimentationEvent
from features.constants import FEATURE_NAME_MAX_LENGTH

# 2020-01-01T00:00:00Z.
MIN_TIMESTAMP_MS = 1_577_836_800_000
MAX_FUTURE_SKEW_HOURS = 24
MAX_EVENT_AGE_DAYS = 10

MAX_EVENT_NAME_CHARS = 256

MAX_VALUE_BYTES = 128 * 1024
MAX_TRAITS_BYTES = 32 * 1024
MAX_METADATA_BYTES = 8 * 1024

EMPTY_BATCH_ERROR = "events must be non-empty"

# axum-core 0.4.5's DEFAULT_LIMIT and its 413 text, which the ingestion server keeps.
MAX_BODY_BYTES = 2_097_152
BODY_LIMIT_ERROR = "Failed to buffer the request body: length limit exceeded"

_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_LONE_SURROGATE_PATTERN = re.compile("[\ud800-\udfff]")


class _StrictCharField(serializers.CharField):
    """Rejects numbers, which CharField would coerce to strings."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # The ingestion server accepts these; to_internal_value cleans them.
        self.validators = [
            validator
            for validator in self.validators
            if not isinstance(
                validator,
                (ProhibitNullCharactersValidator, ProhibitSurrogateCharactersValidator),
            )
        ]

    def to_internal_value(self, data: object) -> str:
        if not isinstance(data, str):
            self.fail("invalid")
        return _clean_text(super().to_internal_value(data))


class _StrictIntegerField(serializers.IntegerField):
    """Rejects booleans, floats and strings, which IntegerField would coerce."""

    def to_internal_value(self, data: object) -> int:
        if isinstance(data, bool) or not isinstance(data, int):
            self.fail("invalid")
        return super().to_internal_value(data)


class SDKExperimentationEventSerializer(serializers.Serializer[dict[str, Any]]):
    """Expects `now` in its context, to bound the timestamp."""

    event = _StrictCharField(max_length=MAX_EVENT_NAME_CHARS, trim_whitespace=False)
    feature_name = _StrictCharField(
        max_length=FEATURE_NAME_MAX_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=True,
        trim_whitespace=False,
    )
    identifier = _StrictCharField(
        max_length=IDENTITY_IDENTIFIER_MAX_LENGTH,
        required=False,
        allow_null=True,
        allow_blank=True,
        trim_whitespace=False,
    )
    timestamp = _StrictIntegerField(min_value=MIN_TIMESTAMP_MS + 1)
    value = serializers.JSONField(required=False, allow_null=True)
    traits = serializers.DictField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, allow_null=True)

    def validate_event(self, name: str) -> str:
        if not name.strip():
            raise serializers.ValidationError("This field may not be blank.")
        if name.startswith("$") and name != EXPOSURE_EVENT_NAME:
            raise serializers.ValidationError("The `$` prefix is reserved.")
        return name

    def validate_timestamp(self, timestamp: int) -> int:
        now: datetime = self.context["now"]
        if timestamp > _to_epoch_ms(now + timedelta(hours=MAX_FUTURE_SKEW_HOURS)):
            raise serializers.ValidationError(
                f"Must be at most {MAX_FUTURE_SKEW_HOURS} hours in the future."
            )
        if timestamp < _to_epoch_ms(now - timedelta(days=MAX_EVENT_AGE_DAYS)):
            raise serializers.ValidationError(
                f"Must be at most {MAX_EVENT_AGE_DAYS} days in the past."
            )
        return timestamp

    def validate_value(self, value: object) -> object:
        return _validate_json_value(value, MAX_VALUE_BYTES)

    def validate_traits(self, traits: dict[str, Any] | None) -> dict[str, Any] | None:
        _validate_json_value(traits, MAX_TRAITS_BYTES)
        for key, value in (traits or {}).items():
            if len(key) > TRAIT_KEY_MAX_LENGTH:
                raise serializers.ValidationError(
                    f"Keys must be at most {TRAIT_KEY_MAX_LENGTH} characters."
                )
            if isinstance(value, str) and len(value) > TRAIT_STRING_VALUE_MAX_LENGTH:
                raise serializers.ValidationError(
                    f"String values must be at most {TRAIT_STRING_VALUE_MAX_LENGTH} characters."
                )
        return traits

    def validate_metadata(self, metadata: object) -> object:
        return _validate_json_value(metadata, MAX_METADATA_BYTES)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["event"] == EXPOSURE_EVENT_NAME and attrs.get("feature_name") is None:
            raise serializers.ValidationError(
                {"feature_name": f"Required for {EXPOSURE_EVENT_NAME} events."}
            )
        return attrs


def is_over_body_limit(content_length: str | None) -> bool:
    """Django reads at most the declared length, so this bounds what is parsed."""
    try:
        return int(content_length or 0) > MAX_BODY_BYTES
    except ValueError:
        return False


def build_sdk_experimentation_event(
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
        timestamp=_UNIX_EPOCH + timedelta(milliseconds=event["timestamp"]),
        collected_at=collected_at,
        identifier=event.get("identifier") or "",
        value=_as_json_column_text(event.get("value")),
        traits=_as_json_column_text(event.get("traits")),
        metadata=_as_json_column_text(event.get("metadata")),
        sdk_language=sdk_language,
        sdk_version=sdk_version,
    )


def _to_epoch_ms(moment: datetime) -> int:
    return (moment - _UNIX_EPOCH) // timedelta(milliseconds=1)


def _validate_json_value(value: object, max_bytes: int) -> object:
    """Measures UTF-8 bytes, as the ingestion server does."""
    try:
        serialised = json.dumps(
            value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
    except ValueError:
        raise serializers.ValidationError("Must not contain non-finite numbers.")
    if len(serialised.encode(errors="surrogatepass")) > max_bytes:
        raise serializers.ValidationError(
            f"Must serialise to at most {max_bytes} bytes."
        )
    return value


def _as_json_column_text(value: object) -> str | None:
    if value is None:
        return None
    return _clean_text(
        value
        if isinstance(value, str)
        else json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    )


def _clean_text(text: str) -> str:
    # PostgreSQL text can't hold NUL, nor UTF-8 a lone surrogate; either fails the batch.
    return _LONE_SURROGATE_PATTERN.sub("\ufffd", text.replace("\x00", ""))
