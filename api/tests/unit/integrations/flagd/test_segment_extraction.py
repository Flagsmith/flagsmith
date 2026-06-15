"""
Tests for the inline-vs-extract decision on segments.

Project-scoped segments referenced by multiple features go into the
top-level ``$evaluators`` block (so the definition is shared). Segments
referenced by exactly one feature are inlined into that feature's
``targeting`` so:

- Single-use segments don't leak their name into a global keyspace.
- Two different feature-scoped segments that happen to share a display
  name don't collide in ``$evaluators``.

These tests exercise the orchestrator (``_build_from_engine``) directly
with synthesised engine models so no DB is needed.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from flag_engine.segments import constants as op
from jsonschema import Draft7Validator
from referencing import Registry, Resource

from integrations.flagd.services import _build_from_engine
from tests.unit.integrations.flagd.test_jsonschema import FIXTURE_DIR
from util.engine_models.environments.models import EnvironmentModel
from util.engine_models.features.models import (
    FeatureModel,
    FeatureSegmentModel,
    FeatureStateModel,
)
from util.engine_models.organisations.models import OrganisationModel
from util.engine_models.projects.models import ProjectModel
from util.engine_models.segments.models import (
    SegmentConditionModel,
    SegmentModel,
    SegmentRuleModel,
)


def _feature(id_: int, name: str) -> FeatureModel:
    return FeatureModel(id=id_, name=name, type="STANDARD")


def _segment(
    *,
    segment_id: int,
    name: str,
    property_: str,
    value: str,
    overrides: list[FeatureStateModel],
) -> SegmentModel:
    return SegmentModel(
        id=segment_id,
        name=name,
        rules=[
            SegmentRuleModel(
                type="ALL",
                conditions=[
                    SegmentConditionModel(
                        operator=op.EQUAL, property_=property_, value=value
                    ),
                ],
            ),
        ],
        feature_states=overrides,
    )


def _override(
    *,
    feature: FeatureModel,
    enabled: bool,
    value: Any,
) -> FeatureStateModel:
    return FeatureStateModel(
        feature=feature,
        enabled=enabled,
        feature_state_value=value,
        feature_segment=FeatureSegmentModel(priority=0),
    )


def _environment(
    *,
    segments: list[SegmentModel],
    feature_states: list[FeatureStateModel],
) -> EnvironmentModel:
    return EnvironmentModel(
        id=1,
        api_key="ser.test",
        project=ProjectModel(
            id=1,
            name="proj",
            organisation=OrganisationModel(
                id=1, name="org", feature_analytics=False, persist_trait_data=False
            ),
            segments=segments,
        ),
        feature_states=feature_states,
    )


def _build(env: EnvironmentModel) -> dict[str, Any]:
    return _build_from_engine(
        env, environment_id=env.id, flag_set_id="proj/env", version="v"
    )


def _validator() -> Draft7Validator:
    main = json.loads((FIXTURE_DIR / "flagd-schema-v0.json").read_text())
    targeting = json.loads((FIXTURE_DIR / "flagd-targeting-v0.json").read_text())
    registry = Registry().with_resources(
        [
            (
                "https://flagd.dev/schema/v0/flags.json",
                Resource.from_contents(main),
            ),
            (
                "https://flagd.dev/schema/v0/targeting.json",
                Resource.from_contents(targeting),
            ),
            ("./targeting.json", Resource.from_contents(targeting)),
        ]
    )
    return Draft7Validator(main, registry=registry)


def test_build_flagd_document__segment_used_by_one_feature__inlined() -> None:
    # Given a single-use segment with one override
    feature = _feature(1, "flag_a")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="default"
    )
    segment = _segment(
        segment_id=10,
        name="single-use",
        property_="email",
        value="alice@acme.com",
        overrides=[_override(feature=feature, enabled=True, value="overridden")],
    )
    env = _environment(segments=[segment], feature_states=[default_fs])

    # When the document is built
    document = _build(env)

    # Then there is no $evaluators block — the segment is inlined.
    assert "$evaluators" not in document
    # And the flag's targeting carries the raw JsonLogic for the segment.
    flag = document["flags"]["flag_a"]
    assert flag["targeting"] == {
        "if": [
            {"==": [{"var": "email"}, "alice@acme.com"]},
            "override_single-use",
            "control",
        ]
    }


def test_build_flagd_document__segment_used_by_two_features__extracted_to_evaluators() -> (
    None
):
    # Given a shared segment with overrides on two features
    feature_a = _feature(1, "flag_a")
    feature_b = _feature(2, "flag_b")
    default_a = FeatureStateModel(
        feature=feature_a, enabled=True, feature_state_value="a-default"
    )
    default_b = FeatureStateModel(
        feature=feature_b, enabled=True, feature_state_value="b-default"
    )
    shared = _segment(
        segment_id=20,
        name="Premium",
        property_="tier",
        value="premium",
        overrides=[
            _override(feature=feature_a, enabled=True, value="a-premium"),
            _override(feature=feature_b, enabled=True, value="b-premium"),
        ],
    )
    env = _environment(segments=[shared], feature_states=[default_a, default_b])

    # When the document is built
    document = _build(env)

    # Then the segment is in $evaluators
    assert document["$evaluators"] == {"Premium": {"==": [{"var": "tier"}, "premium"]}}
    # And both flags reference it by $ref
    for flag_key in ("flag_a", "flag_b"):
        flag = document["flags"][flag_key]
        assert flag["targeting"]["if"][0] == {"$ref": "Premium"}


def test_build_flagd_document__two_feature_scoped_segments_share_name__inlined_no_collision() -> (
    None
):
    # Given two segments that happen to share a display name but live
    # on different features (different IDs, different rules) — the
    # exact scenario the inline strategy is designed to handle.
    feature_a = _feature(1, "flag_a")
    feature_b = _feature(2, "flag_b")
    default_a = FeatureStateModel(
        feature=feature_a, enabled=True, feature_state_value="a"
    )
    default_b = FeatureStateModel(
        feature=feature_b, enabled=True, feature_state_value="b"
    )
    seg_a = _segment(
        segment_id=30,
        name="mail",
        property_="email",
        value="a.com",
        overrides=[_override(feature=feature_a, enabled=True, value="a-special")],
    )
    seg_b = _segment(
        segment_id=31,
        name="mail",
        property_="email",
        value="b.com",
        overrides=[_override(feature=feature_b, enabled=True, value="b-special")],
    )
    env = _environment(segments=[seg_a, seg_b], feature_states=[default_a, default_b])

    # When the document is built
    document = _build(env)

    # Then $evaluators is absent (both segments are single-use, inlined)
    assert "$evaluators" not in document
    # And each flag's targeting carries its own distinct rule even
    # though the two segments share a display name.
    flag_a_logic = document["flags"]["flag_a"]["targeting"]["if"][0]
    flag_b_logic = document["flags"]["flag_b"]["targeting"]["if"][0]
    assert flag_a_logic == {"==": [{"var": "email"}, "a.com"]}
    assert flag_b_logic == {"==": [{"var": "email"}, "b.com"]}


@pytest.mark.parametrize(
    "usage_count, expects_evaluators",
    [(1, False), (2, True), (3, True)],
    ids=["single-use", "double-use", "triple-use"],
)
def test_build_flagd_document__segment_usage_thresholds__extracts_at_count_two_plus(
    usage_count: int, expects_evaluators: bool
) -> None:
    # Given a segment referenced by N features
    features = [_feature(i, f"flag_{i}") for i in range(1, usage_count + 1)]
    defaults = [
        FeatureStateModel(feature=f, enabled=True, feature_state_value="d")
        for f in features
    ]
    segment = _segment(
        segment_id=40,
        name="threshold",
        property_="x",
        value="y",
        overrides=[
            _override(feature=f, enabled=True, value=f"override-{f.id}")
            for f in features
        ],
    )
    env = _environment(segments=[segment], feature_states=defaults)

    # When the document is built
    document = _build(env)

    # Then $evaluators only appears when usage >= 2
    assert ("$evaluators" in document) is expects_evaluators


def test_build_flagd_document__inline_segment_doc__still_passes_flagd_schema() -> None:
    # Given an inline segment (single use)
    feature = _feature(1, "flag_a")
    default_fs = FeatureStateModel(
        feature=feature, enabled=True, feature_state_value="default"
    )
    segment = _segment(
        segment_id=50,
        name="inline",
        property_="email",
        value="alice@acme.com",
        overrides=[_override(feature=feature, enabled=True, value="overridden")],
    )
    env = _environment(segments=[segment], feature_states=[default_fs])

    # When the document is built
    document = _build(env)

    # Then the document still validates against the flagd schema
    errors = sorted(_validator().iter_errors(document), key=lambda e: list(e.path))
    assert not errors, "\n".join(f"{list(e.path)}: {e.message}" for e in errors)
