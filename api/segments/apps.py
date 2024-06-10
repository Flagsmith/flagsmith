from core.apps import BaseAppConfig


class SegmentsConfig(BaseAppConfig):
    name = "segments"
    default = True

    def ready(self) -> None:
        super().ready()

        import segments.tasks  # noqa
