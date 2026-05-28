class AzureDevOpsError(Exception):
    """Base class for all Azure DevOps client errors raised by this package."""


class AzureDevOpsAuthError(AzureDevOpsError):
    """Raised when ADO rejects credentials with 401 or 403."""


class AzureDevOpsNotFoundError(AzureDevOpsError):
    """Raised when ADO returns 404 for a single-resource lookup."""
