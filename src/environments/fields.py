from rest_framework import serializers


class TraitValueField(serializers.Field):
    """
    Custom field to extract the type of the field on deserialization.
    """
    def to_internal_value(self, data):
        return {
            "type": type(data).__name__,
            "value": data
        }

    def to_representation(self, value):
        return value['value'] if isinstance(value, dict) else value
