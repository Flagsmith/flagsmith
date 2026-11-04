from datetime import timedelta

WAREHOUSES_FLAG = "experimentation_warehouses"

EXPOSURE_EVENT_NAME = "$flag_exposure"
"""Emitted by SDKs when an identity is served a variant; ``value`` is the
variant key."""

EXPOSURE_HOURLY_BUCKET_MAX_WINDOW = timedelta(hours=72)

EXPOSURES_REFRESH_MIN_INTERVAL = timedelta(minutes=5)
RESULTS_REFRESH_MIN_INTERVAL = timedelta(minutes=5)

CONTROL_VARIANT_KEY = "control"

# Capped at one: the Java SDK ANDs sub-rules regardless of the rule type, so a
# multi-segment `any` audience would evaluate as `all` under local evaluation.
MAX_AUDIENCE_SEGMENTS = 1

# Below these per-variant floors a metric shows "collecting data" rather than
# inference; sample-ratio is only checked once there is enough traffic to judge.
RESULTS_MIN_IDENTITIES_PER_VARIANT = 50
RESULTS_MIN_CONVERSIONS_PER_VARIANT = 5
SRM_MIN_TOTAL_IDENTITIES = 100

WAREHOUSE_CONNECTION_NAME_MAX_LENGTH = 255

# SDK event limits, matching the ingestion server's.
# 2020-01-01T00:00:00Z.
MIN_TIMESTAMP_MS = 1_577_836_800_000
MAX_FUTURE_SKEW_HOURS = 24
MAX_EVENT_AGE_DAYS = 10
MAX_EVENT_NAME_CHARS = 256
MAX_VALUE_BYTES = 128 * 1024
MAX_TRAITS_BYTES = 32 * 1024
MAX_METADATA_BYTES = 8 * 1024
EMPTY_BATCH_ERROR = "events must be non-empty"
# axum-core 0.4.5's DEFAULT_LIMIT and its 413 text, which the ingestion server keeps.
MAX_BODY_BYTES = 2_097_152
BODY_LIMIT_ERROR = "Failed to buffer the request body: length limit exceeded"
