import typing

from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers

from cohorts.constants import COHORT_CSV_MAX_FILE_SIZE_BYTES
from cohorts.exceptions import CsvFileTooLargeError
from cohorts.models import Cohort, CohortSyncKey
from cohorts.services import create_cohort
from environments.models import Environment
from metadata.serializers import MetadataSerializer, MetadataSerializerMixin
from segments.models import Segment


class _SegmentMetadataHandler(MetadataSerializerMixin):
    # The mixin derives the metadata content type from Meta.model; cohort
    # metadata lives on the managed segment, not on the cohort itself.
    class Meta:
        model = Segment


class CohortSerializer(serializers.ModelSerializer[Cohort]):
    name = serializers.CharField(max_length=2000, source="segment.name")
    description = serializers.CharField(
        source="segment.description", required=False, allow_null=True
    )
    metadata = MetadataSerializer(required=False, many=True, write_only=True)

    class Meta:
        model = Cohort
        fields = (
            "id",
            "uuid",
            "name",
            "description",
            "metadata",
            "segment",
            "source_type",
            "version",
            "created_at",
        )
        read_only_fields = ("segment", "source_type", "version", "created_at")

    def validate(self, attrs: dict[str, typing.Any]) -> dict[str, typing.Any]:
        attrs = super().validate(attrs)
        environment = Environment.objects.get(
            api_key=self.context["view"].kwargs["environment_api_key"]
        )
        project = environment.project
        _SegmentMetadataHandler()._validate_required_metadata(
            project.organisation, attrs.get("metadata", []), project
        )
        return attrs

    def create(self, validated_data: dict[str, typing.Any]) -> Cohort:
        segment_data = validated_data["segment"]
        metadata_data = validated_data.pop("metadata", [])
        cohort = create_cohort(
            environment=validated_data["environment"],
            name=segment_data["name"],
            description=segment_data.get("description"),
        )
        if metadata_data:
            _SegmentMetadataHandler()._update_metadata(cohort.segment, metadata_data)
        return cohort


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
    user_ids = serializers.ListField(
        child=serializers.CharField(validators=[_validate_identifier_byte_length]),
        min_length=1,
    )


class CohortCsvSyncSerializer(serializers.Serializer):  # type: ignore[type-arg]
    file = serializers.FileField()
    identifier_column = serializers.IntegerField(required=False, default=0, min_value=0)
    has_header = serializers.BooleanField(required=False, default=True)

    def validate_file(self, file: UploadedFile) -> UploadedFile:
        if file.size and file.size > COHORT_CSV_MAX_FILE_SIZE_BYTES:
            # Deliberately not a ValidationError: propagates as a 413.
            raise CsvFileTooLargeError()
        return file


class CohortCsvSyncIgnoredRowsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    empty = serializers.IntegerField(min_value=0)
    duplicates = serializers.IntegerField(min_value=0)
    too_long = serializers.IntegerField(min_value=0)


class CohortCsvSyncResultSerializer(serializers.Serializer):  # type: ignore[type-arg]
    version = serializers.IntegerField(min_value=0)
    added = serializers.IntegerField(min_value=0)
    removed = serializers.IntegerField(min_value=0)
    unchanged = serializers.IntegerField(min_value=0)
    ignored = CohortCsvSyncIgnoredRowsSerializer()
