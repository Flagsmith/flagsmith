"""
Unit tests for identity-override translation in
``integrations.flagd.translators.flag.feature_state_to_flagd_flag``.
"""

from typing import Any

from flag_engine.segments import constants as op

from integrations.flagd.constants import WARNING_IDENTITY_OVERRIDE_LIMIT
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


def _feature(id_: int = 1, name: str = "id_flag") -> FeatureModel:
    return FeatureModel(id=id_, name=name, type="STANDARD")


def _identity(
    identifier: str, feature: FeatureModel, *, enabled: bool, value: Any = None
) -> IdentityModel:
    return IdentityModel(
        identifier=identifier,
        environment_api_key="ser.test",
        identity_features=[
            FeatureStateModel(feature=feature, enabled=enabled, feature_state_value=value),
        ],
    )


def test_feature_state_to_flagd_flag__one_identity_override__targeting_wraps_in_if() -> None:
    # Given a feature with a single identity override (enabled=False)
    feature = _feature(name="id_flag")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="ctrl"
    )
    identity = _identity("alice", feature, enabled=False, value="ctrl")
    warnings: list[TranslationWarning] = []

    # When we translate it
    flag = feature_state_to_flagd_flag(
        default_fs,
        feature_key="id_flag",
        segments=[],
        segment_targeting={},
        segment_keys={},
        identity_overrides=[identity],
        identity_override_limit=100,
        warnings=warnings,
    )

    # Then the targeting expression is an "if" comparing targetingKey to alice
    assert flag["targeting"] == {
        "if": [
            {"==": [{"var": "targetingKey"}, "alice"]},
            "off",
            "on",
        ]
    }
    assert warnings == []


def test_feature_state_to_flagd_flag__two_identity_overrides__nested_if_first_wins() -> None:
    # Given a feature with two identity overrides
    feature = _feature(name="id_flag")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="ctrl"
    )
    alice = _identity("alice", feature, enabled=True, value="ctrl")
    bob = _identity("bob", feature, enabled=False, value="ctrl")
    warnings: list[TranslationWarning] = []

    # When we translate it
    flag = feature_state_to_flagd_flag(
        default_fs,
        feature_key="id_flag",
        segments=[],
        segment_targeting={},
        segment_keys={},
        identity_overrides=[alice, bob],
        identity_override_limit=100,
        warnings=warnings,
    )

    # Then the outermost branch checks alice first, falling through to bob
    assert flag["targeting"] == {
        "if": [
            {"==": [{"var": "targetingKey"}, "alice"]},
            "on",
            {
                "if": [
                    {"==": [{"var": "targetingKey"}, "bob"]},
                    "off",
                    "on",
                ]
            },
        ]
    }
    assert warnings == []


def test_feature_state_to_flagd_flag__identity_override_with_multivariate__fallback_is_fractional() -> None:
    # Given a multivariate feature with one identity override
    feature = _feature(id_=2, name="mv_id_flag")
    default_fs = FeatureStateModel(
        feature=feature,
        enabled=True,
        feature_state_value="ctrl",
        multivariate_feature_state_values=[
            MultivariateFeatureStateValueModel(
                id=41,
                multivariate_feature_option=MultivariateFeatureOptionModel(
                    id=411, value="A"
                ),
                percentage_allocation=60,
            ),
        ],
    )
    identity = _identity("alice", feature, enabled=True, value="ctrl")
    warnings: list[TranslationWarning] = []

    # When we translate it
    flag = feature_state_to_flagd_flag(
        default_fs,
        feature_key="mv_id_flag",
        segments=[],
        segment_targeting={},
        segment_keys={},
        identity_overrides=[identity],
        identity_override_limit=100,
        warnings=warnings,
    )

    # Then the identity branch wraps the fractional fallback
    expected_fractional = {
        "fractional": [
            {"cat": [{"var": "targetingKey"}, "mv_id_flag"]},
            ["variant_1", 60.0],
            ["on", 40.0],
        ]
    }
    assert flag["targeting"] == {
        "if": [
            {"==": [{"var": "targetingKey"}, "alice"]},
            "on",
            expected_fractional,
        ]
    }


def test_feature_state_to_flagd_flag__identity_and_segment_override__identity_is_outermost() -> None:
    # Given a feature with both a segment override and an identity override
    feature = _feature(id_=3, name="combo_flag")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="ctrl"
    )
    seg_override = FeatureStateModel(
        feature=feature,
        enabled=False,
        feature_state_value="ctrl",
        feature_segment=FeatureSegmentModel(priority=0),
    )
    segment = SegmentModel(
        id=30,
        name="Premium",
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
        feature_states=[seg_override],
    )
    used: set[str] = set()
    seg_key = slugify_segment_name(segment.name, taken=used)
    seg_targeting = {segment.id: segment_to_jsonlogic(segment)}
    seg_keys = {segment.id: seg_key}
    identity = _identity("alice", feature, enabled=True, value="ctrl")
    warnings: list[TranslationWarning] = []

    # When we translate it
    flag = feature_state_to_flagd_flag(
        default_fs,
        feature_key="combo_flag",
        segments=[segment],
        segment_targeting=seg_targeting,
        segment_keys=seg_keys,
        identity_overrides=[identity],
        identity_override_limit=100,
        warnings=warnings,
    )

    # Then the identity branch is outermost and wraps the segment branch
    assert flag["targeting"] == {
        "if": [
            {"==": [{"var": "targetingKey"}, "alice"]},
            "on",
            {
                "if": [
                    {"$ref": seg_key},
                    "off",
                    "on",
                ]
            },
        ]
    }
    assert warnings == []


def test_feature_state_to_flagd_flag__identity_overrides_exceed_limit__warning_emitted() -> None:
    # Given more identity overrides than the configured limit
    feature = _feature(id_=4, name="capped_flag")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="ctrl"
    )
    identities = [
        _identity("alice", feature, enabled=False, value="ctrl"),
        _identity("bob", feature, enabled=False, value="ctrl"),
        _identity("carol", feature, enabled=False, value="ctrl"),
        _identity("dave", feature, enabled=False, value="ctrl"),
    ]
    warnings: list[TranslationWarning] = []

    # When we translate with identity_override_limit=2
    flag = feature_state_to_flagd_flag(
        default_fs,
        feature_key="capped_flag",
        segments=[],
        segment_targeting={},
        segment_keys={},
        identity_overrides=identities,
        identity_override_limit=2,
        warnings=warnings,
    )

    # Then only the first two identities show up in targeting
    assert flag["targeting"] == {
        "if": [
            {"==": [{"var": "targetingKey"}, "alice"]},
            "off",
            {
                "if": [
                    {"==": [{"var": "targetingKey"}, "bob"]},
                    "off",
                    "on",
                ]
            },
        ]
    }
    # And a single warning is emitted with the dropped count
    assert warnings == [
        TranslationWarning(
            reason=WARNING_IDENTITY_OVERRIDE_LIMIT,
            detail="feature=capped_flag, dropped=2",
        )
    ]
