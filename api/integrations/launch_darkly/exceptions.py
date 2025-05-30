from datetime import datetime


class LaunchDarklyAPIError(Exception):
    """Base exception for LaunchDarkly integration errors."""


class LaunchDarklyRateLimitError(LaunchDarklyAPIError):
    """Exception raised when the LaunchDarkly API rate limit is exceeded."""

    def __init__(self, retry_at: datetime):
        super().__init__()
        self.retry_at = retry_at
