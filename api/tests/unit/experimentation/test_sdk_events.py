from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from experimentation.constants import MAX_BODY_BYTES, MAX_VALUE_BYTES, MIN_TIMESTAMP_MS
from experimentation.sdk_events import (
    SDKExperimentationEventSerializer,
    is_over_body_limit,
)

NOW = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
NOW_MS = int(NOW.timestamp() * 1000)
HOUR_MS = 3_600_000
PURCHASE = {"event": "purchase", "timestamp": NOW_MS}
NOT_A_STRING = ["Not a valid string."]
NOT_AN_INTEGER = ["A valid integer is required."]


@freeze_time(NOW)
@pytest.mark.parametrize(
    "event, expected_errors",
    [
        (
            "purchase",
            {"non_field_errors": ["Invalid data. Expected a dictionary, but got str."]},
        ),
        (
            {},
            {
                "event": ["This field is required."],
                "timestamp": ["This field is required."],
            },
        ),
        ({**PURCHASE, "event": 1}, {"event": NOT_A_STRING}),
        ({**PURCHASE, "event": "   "}, {"event": ["This field may not be blank."]}),
        (
            {**PURCHASE, "event": "a\x00"},
            {"event": ["Null characters are not allowed."]},
        ),
        (
            {**PURCHASE, "event": "e" * 257},
            {"event": ["Ensure this field has no more than 256 characters."]},
        ),
        ({**PURCHASE, "event": "$made_up"}, {"event": ["The `$` prefix is reserved."]}),
        (
            {**PURCHASE, "event": "$flag_exposure"},
            {"feature_name": ["Required for $flag_exposure events."]},
        ),
        ({**PURCHASE, "feature_name": 1}, {"feature_name": NOT_A_STRING}),
        (
            {**PURCHASE, "identifier": "u" * 2001},
            {"identifier": ["Ensure this field has no more than 2000 characters."]},
        ),
        ({**PURCHASE, "timestamp": 1.7e12}, {"timestamp": NOT_AN_INTEGER}),
        ({**PURCHASE, "timestamp": True}, {"timestamp": NOT_AN_INTEGER}),
        (
            {**PURCHASE, "timestamp": MIN_TIMESTAMP_MS},
            {"timestamp": ["Timestamp must be after 2020-01-01."]},
        ),
        (
            {**PURCHASE, "timestamp": NOW_MS + 25 * HOUR_MS},
            {"timestamp": ["Timestamp is too far in the future."]},
        ),
        (
            {**PURCHASE, "timestamp": NOW_MS - 11 * 24 * HOUR_MS},
            {"timestamp": ["Timestamp is older than 10 days."]},
        ),
        (
            {**PURCHASE, "value": "x" * MAX_VALUE_BYTES},
            {"value": ["Must serialise to at most 131072 bytes."]},
        ),
        (
            {**PURCHASE, "value": "a\x00"},
            {"value": ["Null characters are not allowed."]},
        ),
        (
            {**PURCHASE, "value": {"amount": float("inf")}},
            {"value": ["Value must be valid JSON."]},
        ),
        (
            {**PURCHASE, "traits": {"score": float("inf")}},
            {"traits": ["Must not contain non-finite numbers."]},
        ),
        (
            {**PURCHASE, "traits": {"plan": "\ud800"}},
            {"traits": ["Surrogate characters are not allowed."]},
        ),
        (
            {**PURCHASE, "traits": {f"t{i}": "v" * 1900 for i in range(20)}},
            {"traits": ["Must serialise to at most 32768 bytes."]},
        ),
        (
            {**PURCHASE, "traits": ["a"]},
            {"traits": ['Expected a dictionary of items but got type "list".']},
        ),
        (
            {**PURCHASE, "traits": {"k" * 201: 1}},
            {"traits": ["Keys must be at most 200 characters."]},
        ),
        (
            {**PURCHASE, "traits": {"plan": "v" * 2001}},
            {"traits": ["String values must be at most 2000 characters."]},
        ),
        (
            {**PURCHASE, "metadata": {"note": "m" * 9000}},
            {"metadata": ["Must serialise to at most 8192 bytes."]},
        ),
    ],
)
def test_sdk_experimentation_event_serializer__invalid_event__returns_errors(
    event: object,
    expected_errors: dict[str, list[str]],
) -> None:
    # Given
    serializer = SDKExperimentationEventSerializer(data=event)

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert serializer.errors == expected_errors


@freeze_time(NOW)
@pytest.mark.parametrize(
    "event",
    [
        {"event": "$flag_exposure", "feature_name": "checkout", "timestamp": NOW_MS},
        {**PURCHASE, "value": "x" * (MAX_VALUE_BYTES - 2)},
        {**PURCHASE, "identifier": "é" * 2000, "traits": {"plan": "é" * 2000}},
        {**PURCHASE, "timestamp": NOW_MS - 10 * 24 * HOUR_MS + 60_000},
        {
            **PURCHASE,
            "feature_name": None,
            "identifier": None,
            "value": None,
            "traits": None,
            "metadata": None,
        },
    ],
    ids=[
        "exposure",
        "value-at-byte-limit",
        "chars-not-bytes",
        "oldest-allowed",
        "null-optionals",
    ],
)
def test_sdk_experimentation_event_serializer__valid_event__returns_it(
    event: dict[str, object],
) -> None:
    # Given
    serializer = SDKExperimentationEventSerializer(data=event)

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data == event


@pytest.mark.parametrize(
    "content_length, expected",
    [
        (str(MAX_BODY_BYTES), False),
        (str(MAX_BODY_BYTES + 1), True),
        ("x", False),
    ],
)
def test_is_over_body_limit__content_length__true_only_above_limit(
    content_length: str | None,
    expected: bool,
) -> None:
    # Given / When
    result = is_over_body_limit(content_length)

    # Then
    assert result is expected
