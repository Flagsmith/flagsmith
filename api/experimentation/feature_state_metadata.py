from typing import TYPE_CHECKING, Any, Callable

from flagsmith_schemas.api import FeatureStateMetadata
from rest_framework.exceptions import ValidationError

from experimentation.models import Experiment, ExperimentStatus
from features.constants import LIVE_EXPERIMENT_MV_OPTIONS_MESSAGE

if TYPE_CHECKING:  # pragma: no cover
    from environments.models import Environment
    from features.models import FeatureState


def get_live_experiment(
    feature_id: int, environment_id: int | None = None
) -> Experiment | None:
    # Multivariate options belong to the feature, not an environment, so an
    # experiment in any environment locks them. A paused experiment counts:
    # changing the variants before it resumes would skew its results.
    experiments = Experiment.objects.filter(
        feature_id=feature_id,
        status__in=(ExperimentStatus.RUNNING, ExperimentStatus.PAUSED),
    )
    if environment_id is not None:
        experiments = experiments.filter(environment_id=environment_id)
    return experiments.select_related("environment").first()  # type: ignore[no-any-return]


def live_experiment_error(experiment: Experiment) -> ValidationError:
    return ValidationError(
        {
            "detail": LIVE_EXPERIMENT_MV_OPTIONS_MESSAGE.format(
                environment=experiment.environment.name
            )
        }
    )


def check_no_live_experiment(feature_id: int) -> None:
    if experiment := get_live_experiment(feature_id):
        raise live_experiment_error(experiment)


def get_feature_state_metadata_builder(
    environment: "Environment",
) -> Callable[["FeatureState"], dict[str, Any] | None]:
    experiment_by_feature_id = {
        experiment.feature_id: experiment
        for experiment in Experiment.objects.filter(
            environment_id=environment.pk,
            status=ExperimentStatus.RUNNING,
        )
    }

    def build(feature_state: "FeatureState") -> dict[str, Any] | None:
        experiment = experiment_by_feature_id.get(feature_state.feature_id)
        if experiment is None or feature_state.identity_id is not None:
            # Identity overrides are hand-picked, never part of an experiment.
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
