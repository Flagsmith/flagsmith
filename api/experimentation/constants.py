from datetime import timedelta

WAREHOUSE_CONNECTION_FLAG = "experimentation_warehouse_connection"
EXPERIMENT_FLAG = "experimental_flags"

EXPOSURE_EVENT_NAME = "$flag_exposure"
"""Emitted by SDKs when an identity is served a variant; ``value`` is the
variant key."""

EXPOSURE_HOURLY_BUCKET_MAX_WINDOW = timedelta(hours=72)

EXPOSURES_REFRESH_MIN_INTERVAL = timedelta(minutes=5)

CONTROL_VARIANT_KEY = "control"

# Below these per-variant floors a metric shows "collecting data" rather than
# inference; sample-ratio is only checked once there is enough traffic to judge.
RESULTS_MIN_IDENTITIES_PER_VARIANT = 50
RESULTS_MIN_CONVERSIONS_PER_VARIANT = 5
SRM_MIN_TOTAL_IDENTITIES = 100
