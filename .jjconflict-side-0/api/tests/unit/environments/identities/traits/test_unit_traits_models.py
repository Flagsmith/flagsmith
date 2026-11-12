import pytest

from environments.identities.traits.models import Trait


@pytest.mark.parametrize(
    "value, expected_data",
    (
        (1, {"value_type": "int", "integer_value": 1}),
        (0, {"value_type": "int", "integer_value": 0}),
        ("my_string", {"value_type": "unicode", "string_value": "my_string"}),
        (True, {"value_type": "bool", "boolean_value": True}),
        (False, {"value_type": "bool", "boolean_value": False}),
        (123.4, {"value_type": "float", "float_value": 123.4}),
    ),
)
def test_generate_trait_value_data__given_value__returns_expected_data(  # type: ignore[no-untyped-def]
    value, expected_data
):
    # Given / When
    result = Trait.generate_trait_value_data(value)

    # Then
    assert result == expected_data


@pytest.mark.parametrize(
    "deserialized_data, expected_data",
    (
        ({"type": "int", "value": 1}, {"value_type": "int", "integer_value": 1}),
        ({"type": "int", "value": 0}, {"value_type": "int", "integer_value": 0}),
        (
            {"type": "unicode", "value": "my_string"},
            {"value_type": "unicode", "string_value": "my_string"},
        ),
        (
            {"type": "bool", "value": True},
            {"value_type": "bool", "boolean_value": True},
        ),
        (
            {"type": "bool", "value": False},
            {"value_type": "bool", "boolean_value": False},
        ),
        (
            {"type": "float", "value": 123.4},
            {"value_type": "float", "float_value": 123.4},
        ),
    ),
)
def test_generate_trait_value_data__given_deserialized_data__returns_expected_data(  # type: ignore[no-untyped-def]
    deserialized_data, expected_data
):
    # Given / When
    result = Trait.generate_trait_value_data(deserialized_data)

    # Then
    assert result == expected_data


def test_trait_bulk_create__multiple_traits__creates_objects(identity):  # type: ignore[no-untyped-def]
    # Given
    traits = [
        Trait(identity=identity, trait_key="key1"),
        Trait(identity=identity, trait_key="key2"),
    ]

    # When
    Trait.objects.bulk_create(traits)

    # Then
    assert Trait.objects.filter(identity=identity).count() == 2


def test_trait_bulk_delete__existing_traits__deletes_objects(trait):  # type: ignore[no-untyped-def]
    # Given / When
    Trait.objects.filter(identity=trait.identity).delete()

    # Then
    assert Trait.objects.filter(identity=trait.identity).count() == 0
