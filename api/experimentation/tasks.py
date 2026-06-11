from django.utils import timezone
from task_processor.decorators import register_task_handler

from experimentation import ingestion_sync_service
from experimentation.models import Experiment, ExperimentExposures
from experimentation.services import compute_exposures_summary


@register_task_handler()
def add_environment_key_to_ingestion(environment_api_key: str) -> None:
    ingestion_sync_service.set_environment_key(environment_api_key)


@register_task_handler()
def delete_environment_key_from_ingestion(environment_api_key: str) -> None:
    ingestion_sync_service.delete_environment_key(environment_api_key)


@register_task_handler()
def compute_experiment_exposures(experiment_id: int) -> None:
    experiment = (
        Experiment.objects.select_related("environment", "feature")
        .filter(id=experiment_id)
        .first()
    )
    if experiment is None or not experiment.started_at:
        return

    exposures, _ = ExperimentExposures.objects.get_or_create(experiment=experiment)
    if exposures.is_final:
        return

    as_of = experiment.ended_at or timezone.now()
    try:
        summary = compute_exposures_summary(
            environment_key=experiment.environment.api_key,
            feature_name=experiment.feature.name,
            window_start=experiment.started_at,
            window_end=as_of,
        )
    except Exception:
        exposures.record_failure()
        return

    exposures.record_refresh(summary, as_of)
