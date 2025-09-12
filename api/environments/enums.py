import enum


class EnvironmentDocumentCacheMode(enum.Enum):
    PERSISTENT = "PERSISTENT"
    EXPIRING = "EXPIRING"
