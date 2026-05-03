from core.apps import BaseAppConfig


class SegmentMembershipConfig(BaseAppConfig):
    name = "segment_membership"
    default = True

    def ready(self) -> None:
        super().ready()  # type: ignore[no-untyped-call]
        # Import order matters — tasks register with the task_processor at
        # import time, and signals enqueue those tasks.
        from segment_membership import (
            signals,  # noqa: F401
            tasks,  # noqa: F401
        )
