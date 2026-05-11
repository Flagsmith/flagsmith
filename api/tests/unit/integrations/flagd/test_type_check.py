"""
Tests for ``integrations.flagd.translators.type_check``, which spots
flags whose variants would land in different flagd typed-flag schemas.
"""

from __future__ import annotations

import pytest

from integrations.flagd.translators.type_check import (
    WARNING_TYPE_MISMATCH,
    detect_type_mismatch,
)
from util.engine_models.features.models import (
    FeatureModel,
    FeatureStateModel,
    MultivariateFeatureOptionModel,
    MultivariateFeatureStateValueModel,
)
from util.engine_models.identities.models import IdentityModel
from util.engine_models.segments.models import SegmentModel


def _feature(name: str = "f") -> FeatureModel:
    return FeatureModel(id=1, name=name, type="STANDARD")


def _mv(value, percentage: float, id_: int = 1) -> MultivariateFeatureStateValueModel:
    return MultivariateFeatureStateValueModel(
        id=id_,
        multivariate_feature_option=MultivariateFeatureOptionModel(
            id=id_ * 10, value=value
        ),
        percentage_allocation=percentage,
    )


def test_detect_type_mismatch__all_strings__no_warning() -> None:
    # Given a flag whose control + MV options are all strings
    fs = FeatureStateModel(
        feature=_feature(),
        enabled=True,
        feature_state_value="hello",
        multivariate_feature_state_values=[
            _mv("alpha", 50, id_=1),
            _mv("beta", 30, id_=2),
        ],
    )

    # When the type check runs
    warnings = detect_type_mismatch(fs)

    # Then no warning is emitted
    assert warnings == []


@pytest.mark.parametrize(
    "control,mv_value",
    [
        ("hello", 42),
        (1, "two"),
        (True, "yes"),
        ([1, 2], {"x": 1}),
    ],
    ids=["string+number", "number+string", "boolean+string", "array+object"],
)
def test_detect_type_mismatch__mixed_types__emits_warning(
    control, mv_value
) -> None:
    # Given a flag whose values land in different flagd type buckets
    fs = FeatureStateModel(
        feature=_feature("mixed"),
        enabled=True,
        feature_state_value=control,
        multivariate_feature_state_values=[_mv(mv_value, 50)],
    )

    # When the type check runs
    warnings = detect_type_mismatch(fs)

    # Then a single mismatch warning is emitted, listing the types involved
    assert len(warnings) == 1
    assert warnings[0]["reason"] == WARNING_TYPE_MISMATCH
    assert "feature=mixed" in warnings[0]["detail"]
    assert "types=[" in warnings[0]["detail"]


def test_detect_type_mismatch__none_control_value__compatible_with_any_mv() -> None:
    # Given a flag with no control value (boolean-only meaning) but a
    # multivariate option carrying a string
    fs = FeatureStateModel(
        feature=_feature(),
        enabled=True,
        feature_state_value=None,
        multivariate_feature_state_values=[_mv("variant", 50)],
    )

    # When the type check runs
    warnings = detect_type_mismatch(fs)

    # Then no warning — null is compatible with anything
    assert warnings == []


def test_detect_type_mismatch__bool_and_number__counts_as_mismatch() -> None:
    # Given Python treats `True == 1`, we still want booleans and numbers
    # to be distinct flagd types (matching the JSON Schema split).
    fs = FeatureStateModel(
        feature=_feature(),
        enabled=True,
        feature_state_value=True,
        multivariate_feature_state_values=[_mv(1, 50)],
    )

    # When the type check runs
    warnings = detect_type_mismatch(fs)

    # Then we emit a warning — boolean and number are different flagd types
    assert len(warnings) == 1
    assert warnings[0]["reason"] == WARNING_TYPE_MISMATCH


def test_detect_type_mismatch__single_variant__no_warning() -> None:
    # Given a flag with just a control value, no MV options
    fs = FeatureStateModel(
        feature=_feature(),
        enabled=True,
        feature_state_value=42,
    )

    # When the type check runs
    warnings = detect_type_mismatch(fs)

    # Then nothing to warn about
    assert warnings == []


def test_detect_type_mismatch__segment_override_with_different_type__emits_warning() -> None:
    # Given a string flag whose segment override sets a number value
    feature = _feature("seg_mix")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="default"
    )
    segment_override_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value=42
    )
    segment = SegmentModel(
        id=10, name="Premium", feature_states=[segment_override_fs]
    )

    # When the type check runs
    warnings = detect_type_mismatch(default_fs, segments=[segment])

    # Then a mismatch warning is emitted naming both types
    assert len(warnings) == 1
    assert warnings[0]["reason"] == WARNING_TYPE_MISMATCH
    assert "number" in warnings[0]["detail"]
    assert "string" in warnings[0]["detail"]


def test_detect_type_mismatch__identity_override_with_different_type__emits_warning() -> None:
    # Given a string flag whose identity override sets a boolean value
    feature = _feature("id_mix")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="default"
    )
    identity = IdentityModel(
        identifier="alice",
        environment_api_key="ser.test",
        identity_features=[
            FeatureStateModel(
                feature=feature, enabled=True, feature_state_value=True
            ),
        ],
    )

    # When the type check runs
    warnings = detect_type_mismatch(default_fs, identity_overrides=[identity])

    # Then a mismatch warning is emitted
    assert len(warnings) == 1
    assert warnings[0]["reason"] == WARNING_TYPE_MISMATCH
    assert "boolean" in warnings[0]["detail"]
    assert "string" in warnings[0]["detail"]


def test_detect_type_mismatch__override_value_matches_control_type__no_warning() -> None:
    # Given a string flag whose segment override sets a different string
    feature = _feature("seg_match")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="A"
    )
    segment_override_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="B"
    )
    segment = SegmentModel(
        id=11, name="Premium", feature_states=[segment_override_fs]
    )

    # When the type check runs
    warnings = detect_type_mismatch(default_fs, segments=[segment])

    # Then no warning — both values are strings, just different ones
    assert warnings == []
