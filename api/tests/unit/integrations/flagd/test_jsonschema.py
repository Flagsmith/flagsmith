"""
Verify that documents produced by the flagd translator validate against
the official flagd JSON Schema.

The schema is checked into the repository under
``api/integrations/flagd/tests/fixtures/`` so this suite is offline-stable.
Update the fixtures when flagd publishes a new schema version.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource

from environments.models import Environment
from features.models import Feature, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from integrations.flagd.services import build_flagd_document
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule

FIXTURE_DIR = (
    Path(__file__).resolve().parents[4]
    / "integrations"
    / "flagd"
    / "tests"
    / "fixtures"
)


@pytest.fixture(scope="session")
def flagd_validator() -> Draft7Validator:
    main_schema = json.loads(
        (FIXTURE_DIR / "flagd-schema-v0.json").read_text()
    )
    targeting_schema = json.loads(
        (FIXTURE_DIR / "flagd-targeting-v0.json").read_text()
    )
    registry = Registry().with_resources(
        [
            (
                "https://flagd.dev/schema/v0/flags.json",
                Resource.from_contents(main_schema),
            ),
            (
                "https://flagd.dev/schema/v0/targeting.json",
                Resource.from_contents(targeting_schema),
            ),
            ("./targeting.json", Resource.from_contents(targeting_schema)),
        ]
    )
    return Draft7Validator(main_schema, registry=registry)


def _assert_valid(
    document: dict[str, Any], validator: Draft7Validator
) -> None:
    errors = sorted(validator.iter_errors(document), key=lambda e: list(e.path))
    assert not errors, "\n".join(
        f"{list(e.path)}: {e.message}" for e in errors
    )


@pytest.mark.django_db
def test_build_flagd_document__empty_environment__validates_against_schema(
    environment: Environment, flagd_validator: Draft7Validator
) -> None:
    # Given an environment with no features
    # When the document is built
    document = build_flagd_document(environment)
    # Then it validates against the flagd schema
    _assert_valid(document, flagd_validator)
    # And carries flagSetId + version metadata
    flag_set_id = document["metadata"]["flagSetId"]
    assert "/" in flag_set_id  # "<project_id>/<environment_id>"
    assert document["metadata"]["version"]


@pytest.mark.django_db
def test_build_flagd_document__boolean_only_flag__validates_against_schema(
    environment: Environment,
    project: Project,
    flagd_validator: Draft7Validator,
) -> None:
    # Given a boolean-only feature
    feature = Feature.objects.create(
        name="bool_flag", project=project, default_enabled=True
    )
    # When the document is built
    document = build_flagd_document(environment)
    # Then it validates and the flag exposes boolean variants
    _assert_valid(document, flagd_validator)
    assert document["flags"][feature.name]["variants"] == {
        "on": True,
        "off": False,
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "initial_value",
    ["hello", "42", "3.14"],
    ids=["string", "integer", "float"],
)
def test_build_flagd_document__typed_value_flag__validates_against_schema(
    environment: Environment,
    project: Project,
    flagd_validator: Draft7Validator,
    initial_value: str,
) -> None:
    # Given a feature with a typed initial value
    Feature.objects.create(
        name=f"typed_flag_{initial_value}",
        project=project,
        initial_value=initial_value,
    )
    # When the document is built
    document = build_flagd_document(environment)
    # Then it validates against the flagd schema
    _assert_valid(document, flagd_validator)


@pytest.mark.django_db
def test_build_flagd_document__multivariate_flag__validates_against_schema(
    environment: Environment,
    project: Project,
    flagd_validator: Draft7Validator,
) -> None:
    # Given a multivariate feature
    feature = Feature.objects.create(
        name="mv_flag",
        project=project,
        initial_value="control",
        default_enabled=True,
    )
    option_a = MultivariateFeatureOption.objects.create(
        feature=feature,
        string_value="A",
        type="unicode",
        default_percentage_allocation=30,
    )
    option_b = MultivariateFeatureOption.objects.create(
        feature=feature,
        string_value="B",
        type="unicode",
        default_percentage_allocation=20,
    )
    feature_state = FeatureState.objects.get(
        environment=environment, feature=feature
    )
    MultivariateFeatureStateValue.objects.filter(
        feature_state=feature_state
    ).delete()
    MultivariateFeatureStateValue.objects.create(
        feature_state=feature_state,
        multivariate_feature_option=option_a,
        percentage_allocation=30,
    )
    MultivariateFeatureStateValue.objects.create(
        feature_state=feature_state,
        multivariate_feature_option=option_b,
        percentage_allocation=20,
    )
    # When the document is built
    document = build_flagd_document(environment)
    # Then it validates and includes a fractional targeting expression
    _assert_valid(document, flagd_validator)
    targeting = document["flags"][feature.name].get("targeting")
    assert targeting and "fractional" in json.dumps(targeting)


@pytest.mark.django_db
def test_build_flagd_document__segment_with_mixed_rules__validates_against_schema(
    environment: Environment,
    project: Project,
    flagd_validator: Draft7Validator,
) -> None:
    # Given a segment with mixed-operator rules
    Feature.objects.create(
        name="segmented_flag", project=project, initial_value="default"
    )
    segment = Segment.objects.create(name="Premium Customers", project=project)
    parent_rule = SegmentRule.objects.create(segment=segment, type="ALL")
    child_rule = SegmentRule.objects.create(rule=parent_rule, type="ALL")
    Condition.objects.create(
        rule=child_rule,
        operator="EQUAL",
        property="tier",
        value="premium",
    )
    Condition.objects.create(
        rule=child_rule,
        operator="GREATER_THAN_INCLUSIVE",
        property="age",
        value="18",
    )
    # When the document is built
    document = build_flagd_document(environment)
    # Then it validates and exposes the segment under $evaluators
    _assert_valid(document, flagd_validator)
    assert document.get("$evaluators")
    assert any("Premium" in key for key in document["$evaluators"])


@pytest.mark.django_db
def test_build_flagd_document__regex_skipped__warning_serialised_as_string(
    environment: Environment,
    project: Project,
    flagd_validator: Draft7Validator,
) -> None:
    # Given a segment with an unsupported REGEX operator
    Feature.objects.create(name="regex_flag", project=project, initial_value="x")
    segment = Segment.objects.create(name="Email Domain", project=project)
    parent_rule = SegmentRule.objects.create(segment=segment, type="ALL")
    child_rule = SegmentRule.objects.create(rule=parent_rule, type="ALL")
    Condition.objects.create(
        rule=child_rule,
        operator="REGEX",
        property="email",
        value=r".*@example\.com$",
    )
    # When the document is built
    document = build_flagd_document(environment)
    # Then it validates and the warnings field is a JSON-encoded string
    _assert_valid(document, flagd_validator)
    warnings = document["metadata"].get("flagsmith.warnings")
    assert isinstance(warnings, str)
    assert "regex_unsupported" in warnings
