import pytest
from pytest_django import DjangoAssertNumQueries

from environments.identities.models import Identity
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
def test_generate_trait_value_data_for_value(value, expected_data):
    assert Trait.generate_trait_value_data(value) == expected_data


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
def test_generate_trait_value_data_for_deserialized_data(
    deserialized_data, expected_data
):
    assert Trait.generate_trait_value_data(deserialized_data) == expected_data


def test_trait_bulk_create_create_objects(identity):
    # Given
    traits = [
        Trait(identity=identity, trait_key="key1"),
        Trait(identity=identity, trait_key="key2"),
    ]

    # When
    Trait.objects.bulk_create(traits)

    # Then
    assert Trait.objects.filter(identity=identity).count() == 2


def test_trait_bulk_delete_deletes_objects(trait):
    # When
    Trait.objects.filter(identity=trait.identity).delete()

    # Then
    Trait.objects.filter(identity=trait.identity).count() == 0


def test_trait_manager_update_or_create_if_changed_does_not_write_to_db_if_not_changed(
    trait: Trait, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    # When
    with django_assert_num_queries(1):
        returned_trait, created = Trait.objects.update_or_create_if_changed(
            identity=trait.identity,
            trait_key=trait.trait_key,
            defaults={"string_value": trait.string_value},
        )

    # Then
    assert returned_trait == trait
    assert created is False


def test_trait_manager_update_or_create_if_changed_creates_trait_if_not_found(
    identity: Identity, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    # Given
    trait_key = "foo"
    string_value = "bar"

    # When
    with django_assert_num_queries(2):
        created_trait, created = Trait.objects.update_or_create_if_changed(
            identity=identity,
            trait_key=trait_key,
            defaults={"string_value": string_value},
        )

    # Then
    assert created_trait.identity == identity
    assert created_trait.string_value == string_value
    assert created_trait.trait_key == trait_key
    assert created is True


def test_trait_manager_update_or_create_if_changed_updates_trait_if_different(
    trait: Trait, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    # Given
    new_string_value = f"{trait.string_value} updated"

    # When
    with django_assert_num_queries(2):
        updated_trait, created = Trait.objects.update_or_create_if_changed(
            identity=trait.identity,
            trait_key=trait.trait_key,
            defaults={"string_value": new_string_value},
        )

    # Then
    assert updated_trait.identity == trait.identity
    assert updated_trait.string_value == new_string_value
    assert updated_trait.trait_key == trait.trait_key
    assert created is False


def test_trait_manager_update_or_create_updates_trait_if_different(
    trait: Trait, django_assert_num_queries: DjangoAssertNumQueries
) -> None:
    # Given
    new_string_value = f"{trait.string_value} updated"

    # When
    with django_assert_num_queries(2):
        updated_trait, created = Trait.objects.update_or_create(
            identity=trait.identity,
            trait_key=trait.trait_key,
            defaults={"string_value": new_string_value},
        )

    # Then
    assert updated_trait.identity == trait.identity
    assert updated_trait.string_value == new_string_value
    assert updated_trait.trait_key == trait.trait_key
    assert created is False
