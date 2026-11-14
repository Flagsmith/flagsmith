# Feature state types
FEATURE_SEGMENT = "FEATURE_SEGMENT"
IDENTITY = "IDENTITY"
ENVIRONMENT = "ENVIRONMENT"

# Feature state statuses
COMMITTED = "COMMITTED"
DRAFT = "DRAFT"

# Multivariate variant reported when an identity falls through to the control value
CONTROL_VARIANT_KEY = "control"
RESERVED_VARIANT_KEY_MESSAGE = f'"{CONTROL_VARIANT_KEY}" is a reserved variant key.'
LIVE_EXPERIMENT_MV_OPTIONS_MESSAGE = (
    'Variations cannot be changed while an experiment is running or paused in the "{environment}" '
    "environment. Complete the experiment to change them."
)

# Tag filtering strategy
UNION = "UNION"
INTERSECTION = "INTERSECTION"

MAX_32_BIT_INTEGER = 2_147_483_647

FEATURE_NAME_MAX_LENGTH = 2000
