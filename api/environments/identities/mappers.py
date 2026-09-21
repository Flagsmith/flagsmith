from typing import TYPE_CHECKING

from django.db.models import Prefetch, Q

from environments.identities.types import IdentityEvaluationContext
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from features.versioning.versioning_service import get_environment_flags_list
from util.mappers.engine import map_environment_to_evaluation_context

if TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from environments.models import Environment
    from segments.models import Segment


__all__ = ("map_identity_to_evaluation_context",)


def map_identity_to_evaluation_context(
    identity: "Identity",
    *,
    traits: "list[Trait] | None" = None,
    feature_name: str | None = None,
    additional_filters: Q | None = None,
) -> IdentityEvaluationContext:
    """Build the context for evaluating `identity`'s flags."""
    environment: "Environment" = identity.environment
    segments: list["Segment"] = environment.get_segments_from_cache()

    override_filters = Q(identity__isnull=True)
    if identity.pk:
        # The identity is persisted (non-transient).
        # Look for its identity overrides in addition to segment overrides.
        override_filters = Q(identity=identity) | override_filters
    if additional_filters:
        override_filters &= additional_filters

    feature_states = get_environment_flags_list(
        environment=environment,
        feature_name=feature_name,
        additional_filters=override_filters,
        additional_select_related_args=["feature_segment__segment"],
        additional_prefetch_related_args=[
            Prefetch(
                "multivariate_feature_state_values",
                queryset=MultivariateFeatureStateValue.objects.select_related(
                    "multivariate_feature_option"
                ),
            )
        ],
    )

    environment_defaults: list[FeatureState] = []
    identity_overrides: list[FeatureState] = []
    segment_overrides: dict[int, list[FeatureState]] = {}
    mv_fs_values_by_feature_state_id = {}

    for feature_state in feature_states:
        mv_fs_values_by_feature_state_id[feature_state.pk] = (
            feature_state.multivariate_feature_state_values.all()
        )
        if feature_state.identity_id is not None:
            identity_overrides.append(feature_state)
        elif (feature_segment := feature_state.feature_segment) is not None:
            segment_overrides.setdefault(feature_segment.segment_id, []).append(
                feature_state
            )
        else:
            environment_defaults.append(feature_state)

    return IdentityEvaluationContext(
        context=map_environment_to_evaluation_context(
            environment=environment,
            identity=identity,
            traits=traits,
            segments=segments,
            features=environment_defaults,
            segment_overrides=segment_overrides,
            identity_overrides=identity_overrides,
            mv_fs_values_by_feature_state_id=mv_fs_values_by_feature_state_id,
        ),
        feature_states_by_id={
            feature_state.pk: feature_state for feature_state in feature_states
        },
    )
