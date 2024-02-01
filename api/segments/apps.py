from core.apps import BaseAppConfig


class SegmentsConfig(BaseAppConfig):
    name = "segments"

    def ready(self) -> None:
        import segments.tasks  # noqa
