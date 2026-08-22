# How many times an environment document write is deferred while the environments or
# features it covers are still being created, and the base of the exponential backoff
# (in seconds) between those attempts, i.e. 1s, 2s, 4s.
ENVIRONMENT_DOCUMENT_WRITE_MAX_DEFERRALS = 3
ENVIRONMENT_DOCUMENT_WRITE_DEFERRAL_SECONDS = 1

IDENTITY_INTEGRATIONS_RELATION_NAMES = [
    "amplitude_config",
    "heap_config",
    "mixpanel_config",
    "rudderstack_config",
    "segment_config",
    "webhook_config",
]
