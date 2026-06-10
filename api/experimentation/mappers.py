"""Mapping of warehouse exposure rows to the exposures payload.

Pure functions: no Django models, no ClickHouse. Input is the per-variant
per-bucket rows produced by the exposures query; output is the JSON-serialisable
payload persisted on exposure snapshots and served by the exposures API.
"""

import math
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from experimentation.constants import (
    CONTROL_VARIANT_KEY,
    EXPOSURE_HOURLY_BUCKET_MAX_WINDOW,
    MULTIPLE_VARIANT_KEY,
)
from experimentation.dataclasses import ExposureBucket
from experimentation.types import (
    ExposureGranularity,
    ExposuresPayload,
    ExposureTimeseriesPoint,
    ExposureVariantData,
)


def select_exposure_granularity(
    window_start: datetime,
    window_end: datetime,
) -> ExposureGranularity:
    if window_end - window_start <= EXPOSURE_HOURLY_BUCKET_MAX_WINDOW:
        return "hour"
    return "day"


def build_exposures_payload(
    buckets: Sequence[ExposureBucket],
    *,
    window_start: datetime,
    window_end: datetime,
    granularity: ExposureGranularity,
) -> ExposuresPayload:
    included = [b for b in buckets if b.variant != MULTIPLE_VARIANT_KEY]
    excluded_identities = sum(
        b.first_exposed_identities for b in buckets if b.variant == MULTIPLE_VARIANT_KEY
    )
    total_identities = sum(b.first_exposed_identities for b in included)

    return ExposuresPayload(
        total_identities=total_identities,
        excluded_identities=excluded_identities,
        days_of_data=_days_of_data(window_start, window_end),
        variants=_build_variants(included, total_identities),
        timeseries={
            "granularity": granularity,
            "points": _build_timeseries_points(included),
        },
    )


def _days_of_data(window_start: datetime, window_end: datetime) -> int:
    return max(0, math.ceil((window_end - window_start) / timedelta(days=1)))


def _build_variants(
    buckets: Sequence[ExposureBucket],
    total_identities: int,
) -> list[ExposureVariantData]:
    buckets_by_variant: dict[str, list[ExposureBucket]] = {}
    for b in buckets:
        buckets_by_variant.setdefault(b.variant, []).append(b)

    variants: list[ExposureVariantData] = []
    for key, variant_buckets in buckets_by_variant.items():
        identities = sum(b.first_exposed_identities for b in variant_buckets)
        variants.append(
            ExposureVariantData(
                key=key,
                identities=identities,
                share=identities / total_identities if total_identities else 0.0,
                is_control=key == CONTROL_VARIANT_KEY,
            )
        )
    # Control first, then treatments by descending identities, ties
    # alphabetically.
    variants.sort(key=lambda v: (not v["is_control"], -v["identities"], v["key"]))
    return variants


def _build_timeseries_points(
    buckets: Sequence[ExposureBucket],
) -> list[ExposureTimeseriesPoint]:
    running = dict.fromkeys({b.variant for b in buckets}, 0)
    buckets_by_start: dict[datetime, list[ExposureBucket]] = {}
    for b in buckets:
        buckets_by_start.setdefault(b.bucket, []).append(b)

    points: list[ExposureTimeseriesPoint] = []
    for bucket_start in sorted(buckets_by_start):
        for b in buckets_by_start[bucket_start]:
            running[b.variant] += b.first_exposed_identities
        points.append(
            ExposureTimeseriesPoint(
                bucket=_isoformat_utc(bucket_start),
                cumulative_identities=dict(running),
            )
        )
    return points


def _isoformat_utc(value: datetime) -> str:
    """The ClickHouse driver returns naive datetimes; the events table stores
    UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
