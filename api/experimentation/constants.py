from datetime import timedelta

WAREHOUSE_CONNECTION_FLAG = "experimentation_warehouse_connection"
EXPERIMENT_FLAG = "experimental_flags"

EXPOSURE_EVENT_NAME = "$flag_exposure"
"""Emitted by SDKs when an identity is served a variant; ``value`` is the
variant key."""

CONTROL_VARIANT_KEY = "control"
"""The variant key SDKs report for the feature's default serve."""

MULTIPLE_VARIANT_KEY = "$multiple"
"""Sentinel variant for identities exposed to more than one variant."""

EXPOSURE_HOURLY_BUCKET_MAX_WINDOW = timedelta(hours=72)
