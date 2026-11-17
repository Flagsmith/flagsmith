from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.openapi import AutoSchema

from environments.identities.traits.constants import (
    TRAIT_STRING_VALUE_MAX_LENGTH,
)
from environments.identities.traits.openapi import TraitValueFieldExtension


def test_trait_value_field_extension__map_serializer_field__includes_max_length() -> (
    None
):
    # Given
    extension = TraitValueFieldExtension(target=None)  # type: ignore[no-untyped-call]
    generator = SchemaGenerator()  # type: ignore[no-untyped-call]
    auto_schema = AutoSchema()
    auto_schema.registry = generator.registry

    # When
    schema = extension.map_serializer_field(auto_schema, direction="request")

    # Then
    assert schema == {
        "type": ["string", "integer", "number", "boolean"],
        "maxLength": TRAIT_STRING_VALUE_MAX_LENGTH,
        "description": "Can be string, integer, float, or boolean. "
        f"String values must be at most {TRAIT_STRING_VALUE_MAX_LENGTH} characters long.",
    }
