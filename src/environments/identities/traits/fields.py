from rest_framework import serializers

from environments.identities.traits.constants import ACCEPTED_TRAIT_VALUE_TYPES
from features.value_types import STRING
import logging

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

        return {"type": data_type, "value": data}

    def to_representation(self, value):
        return_value = value.get("value") if isinstance(value, dict) else value

        if return_value is None:
            logger.warning("Trait value is not an accepted type. Value was %s" % value)

        return return_value
