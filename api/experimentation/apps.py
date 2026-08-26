from django.apps import AppConfig


class ExperimentationConfig(AppConfig):
    name = "experimentation"

    def ready(self) -> None:
        from experimentation import signals  # noqa: F401
