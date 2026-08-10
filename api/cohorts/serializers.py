import typing

from rest_framework import serializers

from cohorts.models import Cohort
from cohorts.services import create_cohort


class CohortSerializer(serializers.ModelSerializer[Cohort]):
    name = serializers.CharField(max_length=2000, source="segment.name")

    class Meta:
        model = Cohort
        fields = (
            "id",
            "uuid",
            "name",
            "segment",
            "source_type",
            "version",
            "created_at",
        )
        read_only_fields = ("segment", "source_type", "version", "created_at")

    def create(self, validated_data: dict[str, typing.Any]) -> Cohort:
        return create_cohort(
            environment=validated_data["environment"],
            name=validated_data["segment"]["name"],
            user=validated_data["user"],
        )
