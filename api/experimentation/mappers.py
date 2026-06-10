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
    excluded_units = sum(
        b.new_units for b in buckets if b.variant == MULTIPLE_VARIANT_KEY
    )
    total_units = sum(b.new_units for b in included)

    return ExposuresPayload(
        total_units=total_units,
        excluded_units=excluded_units,
        days_of_data=_days_of_data(window_start, window_end),
        variants=_build_variants(included, total_units),
        timeseries={
            "granularity": granularity,
            "points": _build_timeseries_points(included),
        },
    )


def _days_of_data(window_start: datetime, window_end: datetime) -> int:
    return max(0, math.ceil((window_end - window_start) / timedelta(days=1)))


def _build_variants(
    buckets: Sequence[ExposureBucket],
    total_units: int,
) -> list[ExposureVariantData]:
    variants: list[ExposureVariantData] = []
    for key in {b.variant for b in buckets}:
        variant_buckets = [b for b in buckets if b.variant == key]
        units = sum(b.new_units for b in variant_buckets)
        variants.append(
            ExposureVariantData(
                key=key,
                units=units,
                share=units / total_units if total_units else 0.0,
                is_control=key == CONTROL_VARIANT_KEY,
                first_exposure=_isoformat_utc(
                    min(b.first_exposure for b in variant_buckets)
                ),
                last_exposure=_isoformat_utc(
                    max(b.last_exposure for b in variant_buckets)
                ),
            )
        )
    # Control first, then treatments by descending units, ties alphabetically.
    variants.sort(key=lambda v: (not v["is_control"], -v["units"], v["key"]))
    return variants


def _build_timeseries_points(
    buckets: Sequence[ExposureBucket],
) -> list[ExposureTimeseriesPoint]:
    variant_keys = {b.variant for b in buckets}
    running = dict.fromkeys(variant_keys, 0)
    points: list[ExposureTimeseriesPoint] = []
    for bucket_start in sorted({b.bucket for b in buckets}):
        for b in buckets:
            if b.bucket == bucket_start:
                running[b.variant] += b.new_units
        points.append(
            ExposureTimeseriesPoint(
                bucket=_isoformat_utc(bucket_start),
                cumulative_units=dict(running),
            )
        )
    return points


def _isoformat_utc(value: datetime) -> str:
    """The ClickHouse driver returns naive datetimes; the events table stores
    UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
