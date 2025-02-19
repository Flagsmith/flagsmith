from core.apps import BaseAppConfig


class SegmentsConfig(BaseAppConfig):
    name = "segments"
    default = True

    def ready(self) -> None:
        super().ready()  # type: ignore[no-untyped-call]

        import segments.tasks  # noqa
