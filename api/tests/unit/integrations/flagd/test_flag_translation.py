"""
Unit tests for ``integrations.flagd.translators.flag.feature_state_to_flagd_flag``.

These tests build ``FeatureStateModel`` instances directly and verify the
resulting flagd flag dict's ``state``, ``variants``, ``defaultVariant`` and
``targeting`` keys.
"""

from typing import Any

import pytest
from flag_engine.segments import constants as op

from integrations.flagd.translators.flag import feature_state_to_flagd_flag
from integrations.flagd.translators.segment import (
    segment_to_jsonlogic,
    slugify_segment_name,
)
from integrations.flagd.types import TranslationWarning
from util.engine_models.features.models import (
    FeatureModel,
    FeatureSegmentModel,
    FeatureStateModel,
    MultivariateFeatureOptionModel,
    MultivariateFeatureStateValueModel,
)
from util.engine_models.identities.models import IdentityModel
from util.engine_models.segments.models import (
    SegmentConditionModel,
    SegmentModel,
    SegmentRuleModel,
)


def _feature(id_: int = 1, name: str = "my_flag") -> FeatureModel:
    return FeatureModel(id=id_, name=name, type="STANDARD")


def _translate(
    feature_state: FeatureStateModel,
    *,
    feature_key: str | None = None,
    segments: list[SegmentModel] | None = None,
    segment_targeting: dict[int, Any] | None = None,
    segment_keys: dict[int, str] | None = None,
    identity_overrides: list[Any] | None = None,
    identity_override_limit: int = 100,
    warnings: list[TranslationWarning] | None = None,
) -> dict[str, Any]:
    return feature_state_to_flagd_flag(
        feature_state,
        feature_key=feature_key or feature_state.feature.name,
        segments=segments or [],
        segment_targeting=segment_targeting or {},
        segment_keys=segment_keys or {},
        identity_overrides=identity_overrides or [],
        identity_override_limit=identity_override_limit,
        warnings=warnings if warnings is not None else [],
    )


# ---------------------------------------------------------------------------
# Boolean-only flags
# ---------------------------------------------------------------------------


def test_feature_state_to_flagd_flag__boolean_enabled__emits_control_default() -> None:
    # Given a boolean-only enabled feature state
    feature = _feature(name="bool_flag")
    fs = FeatureStateModel(feature=feature, enabled=True, feature_state_value=None)

    # When we translate it
    flag = _translate(fs)

    # Then the flag is ENABLED, defaults to "control", and exposes only the
    # control variant (no disabled overrides means no "off" variant)
    assert flag["state"] == "ENABLED"
    assert flag["defaultVariant"] == "control"
    assert flag["variants"] == {"control": True}
    assert "targeting" not in flag


def test_feature_state_to_flagd_flag__boolean_disabled__state_disabled_default_control() -> (
    None
):
    # Given a boolean-only disabled feature state
    feature = _feature(name="bool_flag")
    fs = FeatureStateModel(feature=feature, enabled=False, feature_state_value=None)

    # When we translate it
    flag = _translate(fs)

    # Then the flag is DISABLED, defaults to "control" (flagd's state field
    # carries the disabled semantic), and only the control variant is emitted
    assert flag["state"] == "DISABLED"
    assert flag["defaultVariant"] == "control"
    assert flag["variants"] == {"control": True}
    assert "targeting" not in flag


# ---------------------------------------------------------------------------
# Boolean + typed value flags
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "control_value",
    ["hello", 42, 3.14, {"key": "value"}, [1, 2, 3]],
    ids=["string", "integer", "float", "json-object", "json-array"],
)
def test_feature_state_to_flagd_flag__typed_value__variants_just_control(
    control_value: Any,
) -> None:
    # Given a feature state with a typed value and no disabled overrides
    feature = _feature(name="typed_flag")
    fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value=control_value
    )

    # When we translate it
    flag = _translate(fs)

    # Then only the "control" variant is emitted (no "off" without a disabled
    # override that needs it)
    assert flag["variants"] == {"control": control_value}
    assert flag["state"] == "ENABLED"
    assert flag["defaultVariant"] == "control"


# ---------------------------------------------------------------------------
# Multivariate flags
# ---------------------------------------------------------------------------


def test_feature_state_to_flagd_flag__multivariate_under_100__residual_routes_to_on() -> (
    None
):
    # Given a multivariate feature state with allocations summing to <100
    feature = _feature(name="mv_flag")
    fs = FeatureStateModel(
        feature=feature,
        enabled=True,
        feature_state_value="control",
        multivariate_feature_state_values=[
            MultivariateFeatureStateValueModel(
                id=11,
                multivariate_feature_option=MultivariateFeatureOptionModel(
                    id=111, value="A"
                ),
                percentage_allocation=30,
            ),
            MultivariateFeatureStateValueModel(
                id=12,
                multivariate_feature_option=MultivariateFeatureOptionModel(
                    id=112, value="B"
                ),
                percentage_allocation=20,
            ),
        ],
    )

    # When we translate it
    flag = _translate(fs)

    # Then variants are indexed (variant_1, variant_2, ...) and no "off" is
    # emitted because there are no disabled overrides
    assert flag["variants"] == {
        "control": "control",
        "variant_1": "A",
        "variant_2": "B",
    }
    # And the targeting carries the fractional bucket so flagd resolves
    # to one of the multivariate variants rather than the static default.
    assert flag["targeting"] == {
        "fractional": [
            {"cat": [{"var": "targetingKey"}, "mv_flag"]},
            ["variant_1", 30.0],
            ["variant_2", 20.0],
            ["control", 50.0],
        ]
    }
    assert flag["state"] == "ENABLED"
    assert flag["defaultVariant"] == "control"


def test_feature_state_to_flagd_flag__multivariate_full_100__no_residual() -> None:
    # Given a multivariate feature state with allocations summing to exactly 100
    feature = _feature(name="mv_flag")
    fs = FeatureStateModel(
        feature=feature,
        enabled=True,
        feature_state_value="control",
        multivariate_feature_state_values=[
            MultivariateFeatureStateValueModel(
                id=21,
                multivariate_feature_option=MultivariateFeatureOptionModel(
                    id=211, value="A"
                ),
                percentage_allocation=20,
            ),
            MultivariateFeatureStateValueModel(
                id=22,
                multivariate_feature_option=MultivariateFeatureOptionModel(
                    id=212, value="B"
                ),
                percentage_allocation=30,
            ),
            MultivariateFeatureStateValueModel(
                id=23,
                multivariate_feature_option=MultivariateFeatureOptionModel(
                    id=213, value="C"
                ),
                percentage_allocation=50,
            ),
        ],
    )

    # When we translate it
    flag = _translate(fs)

    # Then variants are indexed (variant_N) and there's no residual
    assert flag["targeting"] == {
        "fractional": [
            {"cat": [{"var": "targetingKey"}, "mv_flag"]},
            ["variant_1", 20.0],
            ["variant_2", 30.0],
            ["variant_3", 50.0],
        ]
    }
    assert flag["variants"] == {
        "control": "control",
        "variant_1": "A",
        "variant_2": "B",
        "variant_3": "C",
    }


def test_feature_state_to_flagd_flag__multivariate_with_non_string_values__indexed_variant_names() -> (
    None
):
    # Given a multivariate flag whose option values aren't strings
    feature = _feature(name="numeric_mv")
    fs = FeatureStateModel(
        feature=feature,
        enabled=True,
        feature_state_value=0,
        multivariate_feature_state_values=[
            MultivariateFeatureStateValueModel(
                id=31,
                multivariate_feature_option=MultivariateFeatureOptionModel(
                    id=311, value=1
                ),
                percentage_allocation=50,
            ),
            MultivariateFeatureStateValueModel(
                id=32,
                multivariate_feature_option=MultivariateFeatureOptionModel(
                    id=312, value={"foo": "bar"}
                ),
                percentage_allocation=30,
            ),
        ],
    )

    # When we translate it
    flag = _translate(fs)

    # Then variant names are indexed regardless of value type, and no "off"
    # variant is emitted (no disabled overrides)
    assert flag["variants"] == {
        "control": 0,
        "variant_1": 1,
        "variant_2": {"foo": "bar"},
    }


# ---------------------------------------------------------------------------
# No targeting / segment override / disabled
# ---------------------------------------------------------------------------


def test_feature_state_to_flagd_flag__no_segments_no_overrides__targeting_none() -> (
    None
):
    # Given a plain feature state
    feature = _feature(name="plain")
    fs = FeatureStateModel(feature=feature, enabled=True, feature_state_value="x")

    # When we translate it without any segments or identity overrides
    flag = _translate(fs)

    # Then targeting is None
    assert "targeting" not in flag


def test_feature_state_to_flagd_flag__one_segment_override__emits_if_with_ref() -> None:
    # Given a feature with a segment override and the segment-translation
    # bookkeeping the orchestrator would normally produce
    feature = _feature(id_=5, name="seg_flag")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="control"
    )
    override_fs = FeatureStateModel(
        feature=feature,
        enabled=True,
        feature_state_value="premium-value",
        feature_segment=FeatureSegmentModel(priority=0),
    )
    segment = SegmentModel(
        id=10,
        name="Premium tier",
        rules=[
            SegmentRuleModel(
                type="ALL",
                conditions=[
                    SegmentConditionModel(
                        operator=op.EQUAL,
                        property_="tier",
                        value="premium",
                    ),
                ],
            ),
        ],
        feature_states=[override_fs],
    )
    used: set[str] = set()
    seg_key = slugify_segment_name(segment.name, taken=used)
    used.add(seg_key)
    seg_targeting = {segment.id: segment_to_jsonlogic(segment)}
    seg_keys = {segment.id: seg_key}

    # When we translate the default feature state with the override metadata
    flag = _translate(
        default_fs,
        segments=[segment],
        segment_targeting=seg_targeting,
        segment_keys=seg_keys,
    )

    # Then the override's value lives in a synthesised variant and the
    # targeting branches to it when the segment matches.
    expected_variant = f"override_{seg_key}"
    assert flag["variants"] == {"control": "control", expected_variant: "premium-value"}
    assert flag["targeting"] == {
        "if": [
            {"$ref": seg_key},
            expected_variant,
            "control",
        ]
    }


def test_feature_state_to_flagd_flag__disabled_with_targeting__keeps_variants_and_targeting() -> (
    None
):
    # Given a disabled feature state with a segment override
    feature = _feature(id_=7, name="disabled_flag")
    default_fs = FeatureStateModel(
        feature=feature, enabled=False, feature_state_value="ctrl"
    )
    override_fs = FeatureStateModel(
        feature=feature,
        enabled=True,
        feature_state_value="ctrl",
        feature_segment=FeatureSegmentModel(priority=0),
    )
    segment = SegmentModel(
        id=20,
        name="Beta",
        rules=[
            SegmentRuleModel(
                type="ALL",
                conditions=[
                    SegmentConditionModel(
                        operator=op.EQUAL,
                        property_="beta",
                        value="true",
                    ),
                ],
            ),
        ],
        feature_states=[override_fs],
    )
    used: set[str] = set()
    seg_key = slugify_segment_name(segment.name, taken=used)
    seg_targeting = {segment.id: segment_to_jsonlogic(segment)}
    seg_keys = {segment.id: seg_key}

    # When we translate it
    flag = _translate(
        default_fs,
        segments=[segment],
        segment_targeting=seg_targeting,
        segment_keys=seg_keys,
    )

    # Then state is DISABLED, defaultVariant is still "control" (flagd's
    # state field carries the disabled semantic), and the targeting is
    # absent — the override is enabled=True with value == control, so
    # routing collapses to a no-op and is pruned.
    assert flag["state"] == "DISABLED"
    assert flag["variants"] == {"control": "ctrl"}
    assert flag["defaultVariant"] == "control"
    assert "targeting" not in flag


def test_feature_state_to_flagd_flag__name_with_special_chars__feature_key_preserved() -> (
    None
):
    # Given a feature key containing characters that segment slugification
    # would mangle (translator should leave them untouched). We also set an
    # identity override so targeting is built and the bucket seed is
    # surfaced verbatim.
    feature = _feature(id_=9, name="My Flag/With Spaces!")
    fs = FeatureStateModel(
        feature=feature,
        enabled=True,
        feature_state_value="ctrl",
        multivariate_feature_state_values=[
            MultivariateFeatureStateValueModel(
                id=31,
                multivariate_feature_option=MultivariateFeatureOptionModel(
                    id=311, value="A"
                ),
                percentage_allocation=100,
            ),
        ],
    )
    identity = IdentityModel(
        identifier="alice",
        environment_api_key="ser.test",
        identity_features=[
            FeatureStateModel(
                feature=feature, enabled=True, feature_state_value="ctrl"
            ),
        ],
    )

    # When we translate it
    flag = _translate(
        fs,
        feature_key="My Flag/With Spaces!",
        identity_overrides=[identity],
    )

    # Then alice's override is a no-op (enabled=True, value == control)
    # and gets pruned. Targeting collapses to the bare fractional, which
    # uses the feature key verbatim in the bucket seed.
    assert flag["targeting"] == {
        "fractional": [
            {"cat": [{"var": "targetingKey"}, "My Flag/With Spaces!"]},
            ["variant_1", 100.0],
        ]
    }
