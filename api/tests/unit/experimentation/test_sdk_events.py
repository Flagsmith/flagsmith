from datetime import datetime, timedelta, timezone

import pytest

from experimentation.sdk_events import (
    DEFAULT_LIMIT,
    MAX_VALUE_BYTES,
    MIN_TIMESTAMP_MS,
    build_sdk_experimentation_event,
    exceeds_body_limit,
    parse_sdk_user_agent,
    partition_sdk_events,
)

NOW = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
NOW_MS = int(NOW.timestamp() * 1000)
HOUR_MS = 3_600_000
PURCHASE = {"event": "purchase", "timestamp": NOW_MS}


@pytest.mark.parametrize(
    "event, expected_error",
    [
        ("purchase", "events[0] must be an object"),
        ({"timestamp": NOW_MS}, "events[0].event must be non-empty"),
        ({**PURCHASE, "event": 1}, "events[0].event must be a string"),
        ({**PURCHASE, "event": "   "}, "events[0].event must be non-empty"),
        (
            {**PURCHASE, "event": "e" * 257},
            "events[0].event must be at most 256 characters",
        ),
        (
            {**PURCHASE, "event": "$made_up"},
            'events[0].event "$made_up" uses the reserved `$` prefix but is not a known system event',
        ),
        (
            {**PURCHASE, "event": "$flag_exposure"},
            "events[0].feature_name is required for $flag_exposure events",
        ),
        (
            {**PURCHASE, "feature_name": 1},
            "events[0].feature_name must be a string",
        ),
        (
            {**PURCHASE, "identifier": "u" * 2001},
            "events[0].identifier must be at most 2000 characters",
        ),
        (
            {"event": "purchase"},
            "events[0].timestamp must be an epoch-millis value after 2020-01-01",
        ),
        ({**PURCHASE, "timestamp": 1.7e12}, "events[0].timestamp must be an integer"),
        (
            {**PURCHASE, "timestamp": MIN_TIMESTAMP_MS},
            "events[0].timestamp must be an epoch-millis value after 2020-01-01",
        ),
        (
            {**PURCHASE, "timestamp": NOW_MS + 25 * HOUR_MS},
            "events[0].timestamp must not be more than 24h in the future",
        ),
        (
            {**PURCHASE, "timestamp": NOW_MS - 11 * 24 * HOUR_MS},
            "events[0].timestamp must not be more than 10 days in the past",
        ),
        (
            {**PURCHASE, "value": "x" * MAX_VALUE_BYTES},
            "events[0].value must serialize to at most 131072 bytes",
        ),
        (
            {**PURCHASE, "traits": {f"t{i}": "v" * 1900 for i in range(20)}},
            "events[0].traits must serialize to at most 32768 bytes",
        ),
        ({**PURCHASE, "traits": ["a"]}, "events[0].traits must be a JSON object"),
        (
            {**PURCHASE, "traits": {"k" * 201: 1}},
            "events[0].trait keys must be at most 200 characters",
        ),
        (
            {**PURCHASE, "traits": {"plan": "v" * 2001}},
            'events[0].traits["plan"] string values must be at most 2000 characters',
        ),
        (
            {**PURCHASE, "metadata": {"note": "m" * 9000}},
            "events[0].metadata must serialize to at most 8192 bytes",
        ),
    ],
)
def test_partition_sdk_events__invalid_event__rejects_with_error(
    event: object,
    expected_error: str,
) -> None:
    # Given / When
    valid, rejected = partition_sdk_events([event], NOW)

    # Then
    assert valid == []
    assert rejected == [{"index": 0, "error": expected_error}]


@pytest.mark.parametrize(
    "event",
    [
        {"event": "$flag_exposure", "feature_name": "checkout", "timestamp": NOW_MS},
        {**PURCHASE, "value": "x" * (MAX_VALUE_BYTES - 2)},
        {**PURCHASE, "identifier": "é" * 2000, "traits": {"plan": "é" * 2000}},
        {**PURCHASE, "timestamp": NOW_MS - 10 * 24 * HOUR_MS + 60_000},
    ],
    ids=["exposure", "value-at-byte-limit", "chars-not-bytes", "oldest-allowed"],
)
def test_partition_sdk_events__valid_event__keeps_it(
    event: dict[str, object],
) -> None:
    # Given / When
    valid, rejected = partition_sdk_events([event], NOW)

    # Then
    assert valid == [event]
    assert rejected == []


@pytest.mark.parametrize(
    "header, expected",
    [
        ("flagsmith-python-sdk/6.2.3", ("python", "6.2.3")),
        ("flagsmith-js-sdk", ("js", "unknown")),
        ("flagsmith-sdk/1.0.0", ("unknown", "1.0.0")),
        (None, ("unknown", "unknown")),
        (f"flagsmith-{'l' * 400}-sdk/{'9' * 400}", ("l" * 100, "9" * 100)),
    ],
)
def test_parse_sdk_user_agent__header__returns_language_and_version(
    header: str | None,
    expected: tuple[str, str],
) -> None:
    # Given / When
    result = parse_sdk_user_agent(header)

    # Then
    assert result == expected


def test_build_sdk_experimentation_event__event__maps_to_row() -> None:
    # Given
    event = {
        "event": "purchase\x00",
        "timestamp": NOW_MS + 7,
        "value": {"amount": 42},
        "traits": {"plan": "pro"},
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
        None,
        NOW + timedelta(milliseconds=7),
        NOW,
        "",
        '{"amount":42}',
        '{"plan":"pro"}',
        None,
        "python",
        "6.2.3",
    )


@pytest.mark.parametrize(
    "content_length, expected",
    [
        (str(DEFAULT_LIMIT), False),
        (str(DEFAULT_LIMIT + 1), True),
        (None, False),
        ("x", False),
    ],
)
def test_exceeds_body_limit__content_length__compares_with_limit(
    content_length: str | None,
    expected: bool,
) -> None:
    # Given / When
    result = exceeds_body_limit(content_length)

    # Then
    assert result is expected
