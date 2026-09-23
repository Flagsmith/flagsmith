from enum import StrEnum


class LifecycleStage(StrEnum):
    """The lifecycle stage of a feature"""

    NEW = "new"
    LIVE = "live"
    STALE = "stale"
    PERMANENT = "permanent"
    NEEDS_MONITORING = "needs_monitoring"
    TO_REMOVE = "to_remove"
