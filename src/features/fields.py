from rest_framework import serializers


class FeatureSegmentValueField(serializers.Field):
    def to_internal_value(self, data):
        # grab the type of the value and set the context for use
        # in the create / update methods on the serializer
        self.context['value_type'] = type(data).__name__
        return str(data)

    def to_representation(self, value):
        return self.root.instance.get_value()
