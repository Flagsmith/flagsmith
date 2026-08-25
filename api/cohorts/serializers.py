import typing

from rest_framework import serializers

from cohorts.models import Cohort, CohortSyncKey
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


class CohortSyncKeySerializer(serializers.ModelSerializer[CohortSyncKey]):
    key = serializers.SerializerMethodField()
    # The model field carries a default, which DRF would read as optional;
    # saving without a name fails at the database instead.
    name = serializers.CharField(max_length=50)

    class Meta:
        model = CohortSyncKey
        fields = ("prefix", "name", "created", "key")
        read_only_fields = ("prefix", "created")

    def create(self, validated_data: dict[str, typing.Any]) -> CohortSyncKey:
        key, self._generated_key = CohortSyncKey.objects.create_key(**validated_data)
        return typing.cast(CohortSyncKey, key)

    def get_key(self, instance: CohortSyncKey) -> str | None:
        # The plaintext key exists only in the create response; it is
        # unrecoverable afterwards.
        return getattr(self, "_generated_key", None)


class AmplitudeListSerializer(serializers.Serializer[None]):
    name = serializers.CharField(max_length=2000)


def _validate_identifier_byte_length(value: str) -> None:
    # Edge identifiers are DynamoDB sort keys, capped at 1024 bytes.
    if len(value.encode()) > 1024:
        raise serializers.ValidationError(
            "Ensure this identifier has no more than 1024 bytes."
        )


class CohortSyncMembersSerializer(serializers.Serializer[None]):
    # TODO: apply the same byte-length check to CSV uploads.
    user_ids = serializers.ListField(
        child=serializers.CharField(validators=[_validate_identifier_byte_length]),
        min_length=1,
    )
