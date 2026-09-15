from typing import TYPE_CHECKING, Any, Callable

from flagsmith_schemas.api import FeatureStateMetadata

from experimentation.models import Experiment, ExperimentStatus

if TYPE_CHECKING:  # pragma: no cover
    from django.db.models import QuerySet

    from environments.models import Environment
    from features.models import FeatureState


def get_running_experiments_queryset() -> "QuerySet[Experiment]":
    queryset: "QuerySet[Experiment]" = Experiment.objects.filter(
        status=ExperimentStatus.RUNNING,
    )
    return queryset


def get_feature_state_metadata_builder(
    environment: "Environment",
) -> Callable[["FeatureState"], dict[str, Any] | None]:
    if (experiments := getattr(environment, "running_experiments", None)) is None:
        experiments = get_running_experiments_queryset().filter(
            environment_id=environment.pk,
        )
    experiment_by_feature_id = {
        experiment.feature_id: experiment for experiment in experiments
    }

    def build(feature_state: "FeatureState") -> dict[str, Any] | None:
        experiment = experiment_by_feature_id.get(feature_state.feature_id)
        if experiment is None:
            return None
        return dict(
            build_feature_state_metadata(
                experiment,
                in_experiment=is_rollout_segment_override(feature_state, experiment),
            )
        )

    return build


def is_rollout_segment_override(
    feature_state: "FeatureState",
    experiment: Experiment,
) -> bool:
    feature_segment = feature_state.feature_segment
    return (
        experiment.rollout_segment_id is not None
        and feature_segment is not None
        and feature_segment.segment_id == experiment.rollout_segment_id
    )


def build_feature_state_metadata(
    experiment: Experiment,
    *,
    in_experiment: bool,
) -> FeatureStateMetadata:
    return {
        "experiment": {
            "id": experiment.pk,
            "name": experiment.name,
            "in_experiment": in_experiment,
        }
    }
