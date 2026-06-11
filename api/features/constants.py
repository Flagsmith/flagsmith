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

# Tag filtering strategy
UNION = "UNION"
INTERSECTION = "INTERSECTION"

MAX_32_BIT_INTEGER = 2_147_483_647
