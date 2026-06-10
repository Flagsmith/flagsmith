"""Pure mapping of exposure rows to the exposures payload — no Django or
ClickHouse imports here."""

import math
from collections.abc import Sequence
from datetime import datetime, timedelta

from experimentation.constants import (
    CONTROL_VARIANT_KEY,
    MULTIPLE_VARIANT_KEY,
)
from experimentation.dataclasses import ExposureBucket
from experimentation.types import (
    ExposureGranularity,
    ExposuresPayload,
    ExposureTimeseriesPoint,
    ExposureVariantData,
)


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
        variants=_build_variants(included),
        timeseries={
            "granularity": granularity,
            "points": _build_timeseries_points(included),
        },
    )


def _days_of_data(window_start: datetime, window_end: datetime) -> int:
    return max(0, math.ceil((window_end - window_start) / timedelta(days=1)))


def _build_variants(
    buckets: Sequence[ExposureBucket],
) -> list[ExposureVariantData]:
    identities_by_variant: dict[str, int] = {}
    for b in buckets:
        identities_by_variant[b.variant] = (
            identities_by_variant.get(b.variant, 0) + b.first_exposed_identities
        )

    variants = [
        ExposureVariantData(
            key=key,
            identities=identities,
            is_control=key == CONTROL_VARIANT_KEY,
        )
        for key, identities in identities_by_variant.items()
    ]
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
                bucket=bucket_start.isoformat(),
                cumulative_identities=dict(running),
            )
        )
    return points
