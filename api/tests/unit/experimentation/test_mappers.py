from datetime import datetime, timezone

from experimentation.dataclasses import ExposureBucket
from experimentation.mappers import build_exposures_payload


def _bucket(
    variant: str,
    bucket: datetime,
    first_exposed_identities: int,
) -> ExposureBucket:
    return ExposureBucket(
        variant=variant,
        bucket=bucket,
        first_exposed_identities=first_exposed_identities,
    )


def test_build_exposures_payload__multiple_variants__derives_totals() -> None:
    # Given two variants accumulating identities over two daily buckets
    day_1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    day_2 = datetime(2026, 6, 2, tzinfo=timezone.utc)
    buckets = [
        _bucket("control", day_1, 100),
        _bucket("variant_a", day_1, 90),
        _bucket("control", day_2, 50),
        _bucket("variant_a", day_2, 70),
    ]

    # When
    payload = build_exposures_payload(
        buckets,
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 10, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then the totals are derived
    assert payload["total_identities"] == 310
    assert payload["excluded_identities"] == 0
    assert payload["days_of_data"] == 9
    control, variant_a = payload["variants"]
    assert control == {
        "key": "control",
        "identities": 150,
        "is_control": True,
    }
    assert variant_a == {
        "key": "variant_a",
        "identities": 160,
        "is_control": False,
    }


def test_build_exposures_payload__control_not_largest__still_listed_first() -> None:
    # Given a control variant with fewer identities than two treatments
    day = datetime(2026, 6, 1, tzinfo=timezone.utc)
    buckets = [
        _bucket("variant_b", day, 30),
        _bucket("variant_a", day, 20),
        _bucket("control", day, 10),
    ]

    # When
    payload = build_exposures_payload(
        buckets,
        window_start=day,
        window_end=datetime(2026, 6, 8, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then control comes first, treatments follow by descending identities
    assert [v["key"] for v in payload["variants"]] == [
        "control",
        "variant_b",
        "variant_a",
    ]


def test_build_exposures_payload__tied_treatments__ordered_by_key() -> None:
    # Given two treatments with the same identity count
    day = datetime(2026, 6, 1, tzinfo=timezone.utc)
    buckets = [
        _bucket("variant_b", day, 30),
        _bucket("variant_a", day, 30),
    ]

    # When
    payload = build_exposures_payload(
        buckets,
        window_start=day,
        window_end=datetime(2026, 6, 8, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then the tie is broken alphabetically
    assert [v["key"] for v in payload["variants"]] == ["variant_a", "variant_b"]


def test_build_exposures_payload__multiple_sentinel__excluded_and_counted() -> None:
    # Given identities seen in more than one variant, quarantined as $multiple
    day = datetime(2026, 6, 1, tzinfo=timezone.utc)
    buckets = [
        _bucket("control", day, 100),
        _bucket("variant_a", day, 95),
        _bucket("$multiple", day, 5),
    ]

    # When
    payload = build_exposures_payload(
        buckets,
        window_start=day,
        window_end=datetime(2026, 6, 8, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then they are excluded from variants, the total and the timeseries
    assert payload["total_identities"] == 195
    assert payload["excluded_identities"] == 5
    assert [v["key"] for v in payload["variants"]] == ["control", "variant_a"]
    assert all(
        set(point["cumulative_identities"]) == {"control", "variant_a"}
        for point in payload["timeseries"]["points"]
    )


def test_build_exposures_payload__sparse_buckets__cumulative_carries_forward() -> None:
    # Given variants whose identities arrive in different buckets
    day_1 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    day_2 = datetime(2026, 6, 2, tzinfo=timezone.utc)
    buckets = [
        _bucket("control", day_1, 10),
        _bucket("variant_a", day_2, 7),
    ]

    # When
    payload = build_exposures_payload(
        buckets,
        window_start=day_1,
        window_end=datetime(2026, 6, 3, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then every point covers every variant, carrying totals forward
    assert payload["timeseries"] == {
        "granularity": "day",
        "points": [
            {
                "bucket": "2026-06-01T00:00:00+00:00",
                "cumulative_identities": {"control": 10, "variant_a": 0},
            },
            {
                "bucket": "2026-06-02T00:00:00+00:00",
                "cumulative_identities": {"control": 10, "variant_a": 7},
            },
        ],
    }


def test_build_exposures_payload__no_buckets__empty_payload() -> None:
    # Given no exposure data
    # When
    payload = build_exposures_payload(
        [],
        window_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 6, 2, tzinfo=timezone.utc),
        granularity="hour",
    )

    # Then the payload is empty but fully shaped
    assert payload == {
        "total_identities": 0,
        "excluded_identities": 0,
        "days_of_data": 1,
        "variants": [],
        "timeseries": {"granularity": "hour", "points": []},
    }


def test_build_exposures_payload__partial_day_window__days_rounded_up() -> None:
    # Given a window of 3 days and 6 hours
    day = datetime(2026, 6, 1, tzinfo=timezone.utc)

    # When
    payload = build_exposures_payload(
        [],
        window_start=day,
        window_end=datetime(2026, 6, 4, 6, tzinfo=timezone.utc),
        granularity="day",
    )

    # Then the partial day counts as a full one
    assert payload["days_of_data"] == 4
