import pytest
from core.constants import INTEGER, STRING

from environments.identities.traits.models import Trait
from segments.models import (
    EQUAL,
    GREATER_THAN,
    GREATER_THAN_INCLUSIVE,
    IN,
    IS_NOT_SET,
    IS_SET,
    LESS_THAN,
    LESS_THAN_INCLUSIVE,
    MODULO,
    NOT_EQUAL,
    Condition,
)


@pytest.mark.parametrize(
    "operator, trait_value, condition_value, result",
    [
        (EQUAL, "1.0.0", "1.0.0:semver", True),
        (EQUAL, "1.0.0", "1.0.1:semver", False),
        (NOT_EQUAL, "1.0.0", "1.0.0:semver", False),
        (NOT_EQUAL, "1.0.0", "1.0.1:semver", True),
        (GREATER_THAN, "1.0.1", "1.0.0:semver", True),
        (GREATER_THAN, "1.0.0", "1.0.0-beta:semver", True),
        (GREATER_THAN, "1.0.1", "1.2.0:semver", False),
        (GREATER_THAN, "1.0.1", "1.0.1:semver", False),
        (GREATER_THAN, "1.2.4", "1.2.3-pre.2+build.4:semver", True),
        (LESS_THAN, "1.0.0", "1.0.1:semver", True),
        (LESS_THAN, "1.0.0", "1.0.0:semver", False),
        (LESS_THAN, "1.0.1", "1.0.0:semver", False),
        (LESS_THAN, "1.0.0-rc.2", "1.0.0-rc.3:semver", True),
        (GREATER_THAN_INCLUSIVE, "1.0.1", "1.0.0:semver", True),
        (GREATER_THAN_INCLUSIVE, "1.0.1", "1.2.0:semver", False),
        (GREATER_THAN_INCLUSIVE, "1.0.1", "1.0.1:semver", True),
        (LESS_THAN_INCLUSIVE, "1.0.0", "1.0.1:semver", True),
        (LESS_THAN_INCLUSIVE, "1.0.0", "1.0.0:semver", True),
        (LESS_THAN_INCLUSIVE, "1.0.1", "1.0.0:semver", False),
    ],
)
def test_does_identity_match_for_semver_values(
    identity, operator, trait_value, condition_value, result
):
    # Given
    condition = Condition(operator=operator, property="version", value=condition_value)
    traits = [
        Trait(
            trait_key="version",
            string_value=trait_value,
            identity=identity,
        )
    ]
    # Then
    assert condition.does_identity_match(identity, traits) is result


@pytest.mark.parametrize(
    "trait_value, condition_value, result",
    [
        (1, "2|0", False),
        (2, "2|0", True),
        (3, "2|0", False),
        (34.2, "4|3", False),
        (35.0, "4|3", True),
        ("dummy", "3|0", False),
        ("1.0.0", "3|0", False),
        (False, "1|3", False),
    ],
)
def test_does_identity_match_for_modulo_operator(
    identity, trait_value, condition_value, result
):
    condition = Condition(operator=MODULO, property="user_id", value=condition_value)

    trait_value_data = Trait.generate_trait_value_data(trait_value)
    traits = [Trait(trait_key="user_id", identity=identity, **trait_value_data)]

    assert condition.does_identity_match(identity, traits) is result


def test_does_identity_match_is_set_true(identity):
    # Given
    trait_key = "some_property"
    condition = Condition(operator=IS_SET, property=trait_key)
    traits = [Trait(trait_key=trait_key, identity=identity)]

    # Then
    assert condition.does_identity_match(identity, traits) is True


def test_does_identity_match_is_set_false(identity):
    # Given
    trait_key = "some_property"
    condition = Condition(operator=IS_SET, property=trait_key)
    traits = []

    # Then
    assert condition.does_identity_match(identity, traits) is False


def test_does_identity_match_is_not_set_true(identity):
    # Given
    trait_key = "some_property"
    condition = Condition(operator=IS_NOT_SET, property=trait_key)
    traits = [Trait(trait_key=trait_key, identity=identity)]

    # Then
    assert condition.does_identity_match(identity, traits) is False


def test_does_identity_match_is_not_set_false(identity):
    # Given
    trait_key = "some_property"
    condition = Condition(operator=IS_NOT_SET, property=trait_key)
    traits = []

    # Then
    assert condition.does_identity_match(identity, traits) is True


@pytest.mark.parametrize(
    "condition_value, trait_value_type, trait_string_value, trait_integer_value, expected_result",
    (
        ("", STRING, "foo", None, False),
        ("foo,bar", STRING, "foo", None, True),
        ("foo", STRING, "foo", None, True),
        ("1,2,3,4", INTEGER, None, 1, True),
        ("", INTEGER, None, 1, False),
        ("1", INTEGER, None, 1, True),
    ),
)
def test_does_identity_match_in(
    identity,
    condition_value,
    trait_value_type,
    trait_string_value,
    trait_integer_value,
    expected_result,
):
    # Given
    trait_key = "some_property"
    condition = Condition(operator=IN, property=trait_key, value=condition_value)
    traits = [
        Trait(
            trait_key=trait_key,
            identity=identity,
            value_type=trait_value_type,
            string_value=trait_string_value,
            integer_value=trait_integer_value,
        )
    ]

    # Then
    assert condition.does_identity_match(identity, traits) is expected_result
