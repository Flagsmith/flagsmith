import pytest
from rest_framework import serializers

from features.fields import FeatureSegmentValueField
from features.utils import STRING, BOOLEAN, INTEGER


@pytest.mark.parametrize("value, expected_type", [
    ["string", STRING],
    [True, BOOLEAN],
    [False, BOOLEAN],
    [123, INTEGER],
])
def test_feature_segment_field_to_representation(value, expected_type):
    # Given
    class MySerializer(serializers.Serializer):
        my_field = FeatureSegmentValueField()

    # When
    serializer = MySerializer()
    internal_value = serializer.to_internal_value({"my_field": value})

    # Then
    assert internal_value['my_field'] == str(value)
    assert serializer.context['value_type'] == expected_type
