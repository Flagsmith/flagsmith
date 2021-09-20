from unittest import mock

import pytest
from flag_engine.identities.builders import build_identity_dict

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


def test_trait_bulk_create_calls_put_item(identity):
    # Given
    with mock.patch(
        "environments.identities.models.dynamo_identity_table"
    ) as dynamo_identity_table:
        traits = [
            Trait(identity=identity, trait_key="key1"),
            Trait(identity=identity, trait_key="key2"),
        ]

        # When
        Trait.objects.bulk_create(traits)
        # Then
        identity_dict = build_identity_dict(identity)
        dynamo_identity_table.put_item.assert_called_with(Item=identity_dict)


def test_trait_bulk_delete_deletes_objects(trait):
    # When
    Trait.objects.filter(identity=trait.identity).delete()

    # Then
    Trait.objects.filter(identity=trait.identity).count() == 0


def test_trait_bulk_delete_calls_put_item(trait):
    # Given
    with mock.patch(
        "environments.identities.models.dynamo_identity_table"
    ) as dynamo_identity_table:
        # When
        Trait.objects.filter(identity=trait.identity).delete()

        # Then
        identity_dict = build_identity_dict(trait.identity)
        dynamo_identity_table.batch_writer.return_value.__enter__.return_value.put_item.assert_called_with(
            Item=identity_dict
        )
