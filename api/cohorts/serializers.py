import typing

from rest_framework import serializers

from cohorts.models import Cohort
from cohorts.services import create_cohort


class CohortSerializer(serializers.ModelSerializer[Cohort]):
    name = serializers.CharField(max_length=2000, source="segment.name")
    description = serializers.CharField(
        source="segment.description", required=False, allow_null=True
    )

    class Meta:
        model = Cohort
        fields = (
            "id",
            "uuid",
            "name",
            "description",
            "segment",
            "source_type",
            "version",
            "created_at",
        )
        read_only_fields = ("segment", "source_type", "version", "created_at")

    def create(self, validated_data: dict[str, typing.Any]) -> Cohort:
        segment_data = validated_data["segment"]
        return create_cohort(
            environment=validated_data["environment"],
            name=segment_data["name"],
            description=segment_data.get("description"),
        )
