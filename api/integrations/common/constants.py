# Default timeout (in seconds) for outbound HTTP requests made by integration
# wrappers. Without an explicit timeout, ``requests`` waits indefinitely, so an
# unresponsive third-party endpoint can hang the worker thread that dispatches
# the event, leading to resource exhaustion.
INTEGRATION_REQUEST_TIMEOUT_SECONDS = 10
