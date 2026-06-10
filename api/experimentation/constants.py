from datetime import timedelta

WAREHOUSE_CONNECTION_FLAG = "experimentation_warehouse_connection"
EXPERIMENT_FLAG = "experimental_flags"

EXPOSURE_EVENT_NAME = "$flag_exposure"
"""The warehouse event SDKs emit when an identity is served an experiment
variant; its ``value`` is the variant key."""

CONTROL_VARIANT_KEY = "control"
"""The variant key SDKs report for the feature's default serve."""

MULTIPLE_VARIANT_KEY = "$multiple"
"""Sentinel variant for identities exposed to more than one variant; they are
excluded from per-variant results."""

EXPOSURE_HOURLY_BUCKET_MAX_WINDOW = timedelta(hours=72)
"""Up to this window length, exposure time series buckets are hourly; beyond
it, daily."""
