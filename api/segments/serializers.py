from typing import Any, cast

from common.segments.serializers import SegmentSerializer
from rest_framework import serializers
from typing import Any, cast
from segments.models import Segment
from common.segments.serializers import SegmentSerializer


class SegmentSerializerBasic(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Segment
        fields = ("id", "name", "description")


class SegmentListQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    q = serializers.CharField(
        required=False,
        help_text="Search term to find segment with given term in their name",
    )
    identity = serializers.CharField(
        required=False,
        help_text="Optionally provide the id of an identity to get only the segments they match",
    )
    include_feature_specific = serializers.BooleanField(required=False, default=True)

<<<<<<< HEAD
class CloneSegmentSerializer(SegmentSerializer):
    class Meta:
        model = Segment
        fields = ("name", )

    def validate(self, attrs: dict[str, Any]) -> dict[str,Any]:
=======

class CloneSegmentSerializer(SegmentSerializer):
    class Meta:
        model = Segment
        fields = ("name",)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
>>>>>>> d2a22560a4f99251b95ce402d2b5cc35c946c4cb
        if not attrs.get("name"):
            raise serializers.ValidationError("Name is required to clone a segment")
        return attrs

<<<<<<< HEAD
    def create(self, validated_data: dict[str, Any]) -> Segment: 
        name = validated_data.get("name")
        source_segment = self.context.get("source_segment")
        assert source_segment is not None, "Source segment is required to clone a segment"
        return cast(Segment, source_segment.clone(
            name
        ))
=======
    def create(self, validated_data: dict[str, Any]) -> Segment:
        name = validated_data.get("name")
        source_segment = self.context.get("source_segment")
        assert source_segment is not None, (
            "Source segment is required to clone a segment"
        )
        return cast(Segment, source_segment.clone(name))
>>>>>>> d2a22560a4f99251b95ce402d2b5cc35c946c4cb
