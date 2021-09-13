import logging

from rest_framework import serializers

from environments.identities.traits.constants import (
    ACCEPTED_TRAIT_VALUE_TYPES,
    TRAIT_STRING_VALUE_MAX_LENGTH,
)
from features.value_types import STRING

logger = logging.getLogger(__name__)


class TraitValueField(serializers.Field):
    """
    Custom field to extract the type of the field on deserialization.
    """

    def to_internal_value(self, data):
        data_type = type(data).__name__

        if data_type not in ACCEPTED_TRAIT_VALUE_TYPES:
            data = str(data)
            data_type = STRING
        if data_type == STRING and len(data) > TRAIT_STRING_VALUE_MAX_LENGTH:
            raise serializers.ValidationError(
                f"Value string is too long. Must be less than {TRAIT_STRING_VALUE_MAX_LENGTH} character"
            )
        return {"type": data_type, "value": data}

    def to_representation(self, value):
        return_value = value.get("value") if isinstance(value, dict) else value

        if return_value is None:
            logger.warning("Trait value is not an accepted type. Value was %s" % value)

        return return_value
