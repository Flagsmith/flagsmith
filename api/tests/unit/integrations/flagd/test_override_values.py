"""
Tests for the override-value preservation feature.

flagd's targeting can only return variant *names*; literal values
returned from JsonLogic are interpreted as variant keys. So when a
Flagsmith segment or identity override sets a value that differs from
the flag's control value, the translator must synthesise a per-override
variant carrying that value, then route the targeting branch to it.
"""

from __future__ import annotations

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
)
from util.engine_models.identities.models import IdentityModel
from util.engine_models.segments.models import (
    SegmentConditionModel,
    SegmentModel,
    SegmentRuleModel,
)


def _feature(id_: int = 1, name: str = "f") -> FeatureModel:
    return FeatureModel(id=id_, name=name, type="STANDARD")


def _segment_with_override(
    *,
    segment_id: int,
    segment_name: str,
    feature: FeatureModel,
    enabled: bool,
    value: Any,
) -> SegmentModel:
    override_fs = FeatureStateModel(
        feature=feature,
        enabled=enabled,
        feature_state_value=value,
        feature_segment=FeatureSegmentModel(priority=0),
    )
    return SegmentModel(
        id=segment_id,
        name=segment_name,
        rules=[
            SegmentRuleModel(
                type="ALL",
                conditions=[
                    SegmentConditionModel(
                        operator=op.EQUAL, property_="tier", value="x"
                    ),
                ],
            ),
        ],
        feature_states=[override_fs],
    )


def _identity_with_override(
    *,
    identifier: str,
    feature: FeatureModel,
    enabled: bool,
    value: Any,
) -> IdentityModel:
    return IdentityModel(
        identifier=identifier,
        environment_api_key="ser.test",
        identity_features=[
            FeatureStateModel(
                feature=feature, enabled=enabled, feature_state_value=value
            ),
        ],
    )


def _translate(
    fs: FeatureStateModel,
    *,
    segments: list[SegmentModel] | None = None,
    identity_overrides: list[IdentityModel] | None = None,
) -> dict[str, Any]:
    used: set[str] = set()
    segments = segments or []
    segment_targeting: dict[int, Any] = {}
    segment_keys: dict[int, str] = {}
    for segment in segments:
        slug = slugify_segment_name(segment.name, taken=used)
        used.add(slug)
        segment_keys[segment.id] = slug
        segment_targeting[segment.id] = segment_to_jsonlogic(segment)
    warnings: list[TranslationWarning] = []
    return feature_state_to_flagd_flag(
        fs,
        feature_key=fs.feature.name,
        segments=segments,
        segment_targeting=segment_targeting,
        segment_keys=segment_keys,
        identity_overrides=identity_overrides or [],
        identity_override_limit=100,
        warnings=warnings,
    )


def test_feature_state_to_flagd_flag__segment_override_with_different_value__synthesises_variant() -> None:
    # Given a string flag whose Premium segment override sets a
    # different string value
    feature = _feature(name="seg_value")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="A"
    )
    segment = _segment_with_override(
        segment_id=10,
        segment_name="Premium",
        feature=feature,
        enabled=True,
        value="B",
    )

    # When we translate it
    flag = _translate(default_fs, segments=[segment])

    # Then a new variant is minted carrying the override's value
    assert flag["variants"] == {"control": "A", "override_Premium": "B"}
    # And the targeting branches to that variant when the segment matches
    assert flag["targeting"] == {
        "if": [
            {"$ref": "Premium"},
            "override_Premium",
            "control",
        ]
    }


def test_feature_state_to_flagd_flag__identity_override_with_different_value__synthesises_variant() -> None:
    # Given a string flag whose Alice override sets a different value
    feature = _feature(name="id_value")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="A"
    )
    identity = _identity_with_override(
        identifier="alice", feature=feature, enabled=True, value="B"
    )

    # When we translate it
    flag = _translate(default_fs, identity_overrides=[identity])

    # Then the override's value lives in a synthesised variant and the
    # targeting routes to it
    assert flag["variants"] == {"control": "A", "override_alice": "B"}
    assert flag["targeting"] == {
        "if": [
            {"==": [{"var": "targetingKey"}, "alice"]},
            "override_alice",
            "control",
        ]
    }


def test_feature_state_to_flagd_flag__override_value_equals_control__no_extra_variant() -> None:
    # Given a string flag whose Premium segment override carries the
    # same value as the default
    feature = _feature(name="seg_same")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="A"
    )
    segment = _segment_with_override(
        segment_id=11,
        segment_name="Premium",
        feature=feature,
        enabled=True,
        value="A",
    )

    # When we translate it
    flag = _translate(default_fs, segments=[segment])

    # Then no extra variant is minted — the override is effectively a no-op
    assert flag["variants"] == {"control": "A"}
    # And the targeting collapses to None (segment branch and fallback
    # are both "control")
    assert "targeting" not in flag


def test_feature_state_to_flagd_flag__disabled_override_with_distinct_value__routes_to_value() -> None:
    # Given a segment override that's disabled but carries a distinct
    # value. The new model treats override.enabled as decorative for
    # flagd consumers; only the typed value flows through.
    feature = _feature(name="seg_disabled_value")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="A"
    )
    segment = _segment_with_override(
        segment_id=12,
        segment_name="BlockedUsers",
        feature=feature,
        enabled=False,
        value="blocked-value",
    )

    # When we translate it
    flag = _translate(default_fs, segments=[segment])

    # Then a per-override variant carrying the override's value is
    # minted and the targeting routes to it. No ``off`` variant.
    assert flag["variants"] == {
        "control": "A",
        "override_BlockedUsers": "blocked-value",
    }
    assert flag["targeting"] == {
        "if": [
            {"$ref": "BlockedUsers"},
            "override_BlockedUsers",
            "control",
        ]
    }


def test_feature_state_to_flagd_flag__disabled_override_value_equals_control__warns() -> None:
    # Given a disabled override whose value equals the control —
    # invisible to flagd consumers, so we emit a translation warning.
    from integrations.flagd.constants import WARNING_DISABLED_OVERRIDE_NO_OP

    feature = _feature(name="seg_no_op")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="A"
    )
    segment = _segment_with_override(
        segment_id=13,
        segment_name="Misconfigured",
        feature=feature,
        enabled=False,
        value="A",
    )
    used: set[str] = set()
    seg_key = slugify_segment_name(segment.name, taken=used)
    seg_targeting = {segment.id: segment_to_jsonlogic(segment)}
    seg_keys = {segment.id: seg_key}
    warnings: list[TranslationWarning] = []

    # When we translate it
    feature_state_to_flagd_flag(
        default_fs,
        feature_key="seg_no_op",
        segments=[segment],
        segment_targeting=seg_targeting,
        segment_keys=seg_keys,
        identity_overrides=[],
        identity_override_limit=100,
        warnings=warnings,
    )

    # Then we get a no-op warning naming the segment
    assert any(
        w["reason"] == WARNING_DISABLED_OVERRIDE_NO_OP
        and "Misconfigured" in w["detail"]
        for w in warnings
    )


@pytest.mark.parametrize(
    "name,expected_variant",
    [
        ("Premium Customers!", "override_Premium-Customers"),
        ("  spaced  ", "override_spaced"),
        ("---weird---", "override_weird"),
    ],
)
def test_feature_state_to_flagd_flag__segment_name_special_chars__slugified(
    name: str, expected_variant: str
) -> None:
    # Given an override on a segment with a tricky name
    feature = _feature(name="slug_test")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="A"
    )
    segment = _segment_with_override(
        segment_id=20,
        segment_name=name,
        feature=feature,
        enabled=True,
        value="B",
    )

    # When we translate it
    flag = _translate(default_fs, segments=[segment])

    # Then the variant name is slugified
    assert expected_variant in flag["variants"]
    assert flag["variants"][expected_variant] == "B"


def test_feature_state_to_flagd_flag__two_overrides_with_distinct_values__two_variants() -> None:
    # Given a flag with two segment overrides setting different values
    feature = _feature(id_=2, name="multi_override")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="default"
    )
    seg_a = _segment_with_override(
        segment_id=30,
        segment_name="Premium",
        feature=feature,
        enabled=True,
        value="premium-value",
    )
    seg_b = _segment_with_override(
        segment_id=31,
        segment_name="Trial",
        feature=feature,
        enabled=True,
        value="trial-value",
    )

    # When we translate it
    flag = _translate(default_fs, segments=[seg_a, seg_b])

    # Then both override values are preserved in their own variants
    assert flag["variants"] == {
        "control": "default",
        "override_Premium": "premium-value",
        "override_Trial": "trial-value",
    }
