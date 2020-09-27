from rest_framework import serializers

from features.constants import INTEGER, BOOLEAN, STRING


class FeatureSegmentValueField(serializers.Field):
    def to_internal_value(self, data):
        if data is not None:
            # grab the type of the value and set the context for use
            # in the create / update methods on the serializer
            value_type = type(data).__name__
            value_types = [STRING, BOOLEAN, INTEGER]
            value_type = value_type if value_type in value_types else STRING
            self.context['value_type'] = value_type

            return str(data)

    def to_representation(self, value):
        return self.root.instance.get_value()
