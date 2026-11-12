"""Accepts the payload and limits of https://github.com/Flagsmith/ingestion-server/blob/main/src/routes/ingest.rs, with DRF-style error messages."""

import json
from datetime import timedelta
from typing import Any

from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from environments.identities.constants import IDENTITY_IDENTIFIER_MAX_LENGTH
from environments.identities.traits.constants import (
    TRAIT_KEY_MAX_LENGTH,
    TRAIT_STRING_VALUE_MAX_LENGTH,
)
from experimentation.constants import (
    EXPOSURE_EVENT_NAME,
    MAX_BODY_BYTES,
    MAX_EVENT_AGE_DAYS,
    MAX_EVENT_NAME_CHARS,
    MAX_FUTURE_SKEW_HOURS,
    MAX_METADATA_BYTES,
    MAX_TRAITS_BYTES,
    MAX_VALUE_BYTES,
    MIN_TIMESTAMP_MS,
)
from features.constants import FEATURE_NAME_MAX_LENGTH


class _StrictCharField(serializers.CharField):
    """Rejects numbers, which CharField would coerce to strings."""

    def to_internal_value(self, data: object) -> str:
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)


class _StrictIntegerField(serializers.IntegerField):
    """Rejects booleans, floats and strings, which IntegerField would coerce."""

    def to_internal_value(self, data: object) -> int:
        if isinstance(data, bool) or not isinstance(data, int):
            self.fail("invalid")
        return super().to_internal_value(data)


class SDKExperimentationEventSerializer(serializers.Serializer[dict[str, Any]]):
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
    timestamp = _StrictIntegerField()
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
        now = timezone.now()
        if timestamp <= MIN_TIMESTAMP_MS:
            raise serializers.ValidationError("Timestamp must be after 2020-01-01.")
        if (
            timestamp
            > (now + timedelta(hours=MAX_FUTURE_SKEW_HOURS)).timestamp() * 1000
        ):
            raise serializers.ValidationError("Timestamp is too far in the future.")
        if timestamp < (now - timedelta(days=MAX_EVENT_AGE_DAYS)).timestamp() * 1000:
            raise serializers.ValidationError(
                f"Timestamp is older than {MAX_EVENT_AGE_DAYS} days."
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


@extend_schema_field(SDKExperimentationEventSerializer(many=True))
class _SDKEventListField(serializers.ListField):
    """Leaves each event to SDKExperimentationEventSerializer, so one bad event doesn't fail the batch."""


class SDKExperimentationEventBatchSerializer(serializers.Serializer[dict[str, Any]]):
    events = _SDKEventListField(allow_empty=False)


def is_over_body_limit(content_length: str | None) -> bool:
    """Django reads at most the declared length, so this bounds what is parsed."""
    try:
        return int(content_length or 0) > MAX_BODY_BYTES
    except ValueError:
        return False


def _validate_json_value(value: object, max_bytes: int) -> object:
    """Measures UTF-8 bytes, as the ingestion server does."""
    try:
        serialised = json.dumps(
            value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode()
    except UnicodeEncodeError:
        raise serializers.ValidationError("Surrogate characters are not allowed.")
    except ValueError:
        raise serializers.ValidationError("Must not contain non-finite numbers.")
    if isinstance(value, str) and "\x00" in value:
        raise serializers.ValidationError("Null characters are not allowed.")
    if len(serialised) > max_bytes:
        raise serializers.ValidationError(
            f"Must serialise to at most {max_bytes} bytes."
        )
    return value
