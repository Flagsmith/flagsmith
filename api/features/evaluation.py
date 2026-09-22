from typing import TYPE_CHECKING

from flag_engine.segments.evaluator import get_flag_result_from_context

from util.mappers.engine import FlagResult, map_feature_state_to_feature_context

if TYPE_CHECKING:
    from features.models import FeatureState


__all__ = ("evaluate_feature_state",)


def evaluate_feature_state(
    feature_state: "FeatureState",
    identity_key: str,
) -> FlagResult:
    """Evaluate a single feature state for an identity, ignoring overrides.

    For callers holding one feature state already known to be the right one,
    where the only thing left to resolve is multivariate allocation. Prefer
    `Identity.get_all_feature_states`, which evaluates the whole environment
    and so can apply segment and identity overrides too.
    """
    return get_flag_result_from_context(
        context={
            "environment": {"key": "", "name": ""},
            "identity": {"identifier": "", "key": identity_key},
        },
        feature_context=map_feature_state_to_feature_context(
            feature_state,
            mv_fs_values=feature_state.multivariate_feature_state_values.all(),
        ),
        reason="DEFAULT",
    )
