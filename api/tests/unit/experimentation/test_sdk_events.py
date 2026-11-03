from datetime import datetime, timedelta, timezone

import pytest

from experimentation.sdk_events import (
    MAX_BODY_BYTES,
    MAX_VALUE_BYTES,
    MIN_TIMESTAMP_MS,
    SDKExperimentationEventSerializer,
    build_sdk_experimentation_event,
    is_over_body_limit,
)

NOW = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
NOW_MS = int(NOW.timestamp() * 1000)
HOUR_MS = 3_600_000
PURCHASE = {"event": "purchase", "timestamp": NOW_MS}
NOT_A_STRING = ["Not a valid string."]
NOT_AN_INTEGER = ["A valid integer is required."]


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
            {
                "timestamp": [
                    "Ensure this value is greater than or equal to 1577836800001."
                ]
            },
        ),
        (
            {**PURCHASE, "timestamp": NOW_MS + 25 * HOUR_MS},
            {"timestamp": ["Must be at most 24 hours in the future."]},
        ),
        (
            {**PURCHASE, "timestamp": NOW_MS - 11 * 24 * HOUR_MS},
            {"timestamp": ["Must be at most 10 days in the past."]},
        ),
        (
            {**PURCHASE, "value": "x" * MAX_VALUE_BYTES},
            {"value": ["Must serialise to at most 131072 bytes."]},
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
    serializer = SDKExperimentationEventSerializer(data=event, context={"now": NOW})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert serializer.errors == expected_errors


@pytest.mark.parametrize(
    "event",
    [
        {"event": "$flag_exposure", "feature_name": "checkout", "timestamp": NOW_MS},
        {**PURCHASE, "value": "x" * (MAX_VALUE_BYTES - 2)},
        {**PURCHASE, "identifier": "é" * 2000, "traits": {"plan": "é" * 2000}},
        {**PURCHASE, "timestamp": NOW_MS - 10 * 24 * HOUR_MS + 60_000},
        {**PURCHASE, "event": "purchase\x00", "feature_name": "checkout\ud800"},
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
        "nul-and-lone-surrogate",
        "null-optionals",
    ],
)
def test_sdk_experimentation_event_serializer__valid_event__returns_it(
    event: dict[str, object],
) -> None:
    # Given
    serializer = SDKExperimentationEventSerializer(data=event, context={"now": NOW})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data == event


def test_build_sdk_experimentation_event__json_values_nul_and_lone_surrogate__maps_to_row() -> (
    None
):
    # Given
    event = {
        "event": "purchase\x00",
        "feature_name": "checkout\ud800",
        "timestamp": NOW_MS + 7,
        "value": {"amount": 42},
        "traits": {"plan": "pró"},
    }

    # When
    row = build_sdk_experimentation_event(
        event,
        environment_key="env-key",
        collected_at=NOW,
        sdk_language="python",
        sdk_version="6.2.3",
    )

    # Then
    assert (
        row.environment_key,
        row.event,
        row.feature_name,
        row.timestamp,
        row.collected_at,
        row.identifier,
        row.value,
        row.traits,
        row.metadata,
        row.sdk_language,
        row.sdk_version,
    ) == (
        "env-key",
        "purchase",
        "checkout�",
        NOW + timedelta(milliseconds=7),
        NOW,
        "",
        '{"amount":42}',
        '{"plan":"pró"}',
        None,
        "python",
        "6.2.3",
    )


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
