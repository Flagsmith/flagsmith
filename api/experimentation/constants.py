from datetime import timedelta

WAREHOUSE_CONNECTION_FLAG = "experimentation_warehouse_connection"
EXPERIMENT_FLAG = "experimental_flags"

EXPOSURE_EVENT_NAME = "$flag_exposure"
"""Emitted by SDKs when an identity is served a variant; ``value`` is the
variant key."""

EXPOSURE_HOURLY_BUCKET_MAX_WINDOW = timedelta(hours=72)

EXPOSURES_REFRESH_MIN_INTERVAL = timedelta(minutes=5)
