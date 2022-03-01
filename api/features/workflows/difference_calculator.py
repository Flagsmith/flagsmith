import typing
from dataclasses import dataclass, field

from features.models import FeatureState


@dataclass
class Diff:
    from_: typing.Any
    to: typing.Any


@dataclass
class FeatureStateDiff:
    enabled: Diff = None
    feature_state_value: Diff = None
    multivariate_feature_state_values: typing.Dict[int, Diff] = field(
        default_factory=dict
    )


def get_diff(from_: FeatureState, to: FeatureState) -> FeatureStateDiff:
    return FeatureStateDiff(
        enabled=_get_enabled_diff(from_, to),
        feature_state_value=_get_feature_state_value_diff(from_, to),
        multivariate_feature_state_values=_get_multivariate_feature_state_values_diff(
            from_, to
        ),
    )


def _get_enabled_diff(from_: FeatureState, to: FeatureState) -> typing.Optional[Diff]:
    return (
        Diff(from_=from_.enabled, to=to.enabled)
        if to.enabled != from_.enabled
        else None
    )


def _get_feature_state_value_diff(
    from_: FeatureState, to: FeatureState
) -> typing.Optional[Diff]:
    from_value = from_.get_feature_state_value()
    to_value = to.get_feature_state_value()
    return Diff(from_=from_value, to=to_value) if to_value != from_value else None


def _get_multivariate_feature_state_values_diff(
    from_: FeatureState, to: FeatureState
) -> typing.Dict[int, Diff]:
    diff = {}

    def sort(mv_value):
        return mv_value.multivariate_feature_option_id

    from_mv_values = sorted(from_.multivariate_feature_state_values.all(), key=sort)
    to_mv_values = sorted(to.multivariate_feature_state_values.all(), key=sort)
    assert len(from_mv_values) == len(
        to_mv_values
    ), "Number of MV values must be the same!"

    for i, from_mv_value in enumerate(from_mv_values):
        to_mv_value = to_mv_values[i]
        mv_feature_option_id = from_mv_value.multivariate_feature_option_id
        assert mv_feature_option_id == to_mv_value.multivariate_feature_option_id
        if to_mv_value.percentage_allocation != from_mv_value.percentage_allocation:
            diff[mv_feature_option_id] = Diff(
                from_=from_mv_value.percentage_allocation,
                to=to_mv_value.percentage_allocation,
            )

    return diff
