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


class MixpanelMemberSerializer(serializers.Serializer[None]):
    # Length mirrors CohortMembership.identifier.
    mixpanel_distinct_id = serializers.CharField(max_length=2000)


class MixpanelParametersSerializer(serializers.Serializer[None]):
    mixpanel_cohort_id = serializers.CharField(max_length=255)
    mixpanel_cohort_name = serializers.CharField(max_length=2000)
    # An empty page is valid: a first sync of an empty cohort has no members.
    members = MixpanelMemberSerializer(many=True, allow_empty=True)


class MixpanelWebhookSerializer(serializers.Serializer[None]):
    # "members" carries the full membership on the first sync;
    # "add_members"/"remove_members" carry changes since the last sync.
    action = serializers.ChoiceField(
        choices=["members", "add_members", "remove_members"]
    )
    parameters = MixpanelParametersSerializer()


class CohortSyncMembersSerializer(serializers.Serializer[None]):
    # Child length mirrors CohortMembership.identifier.
    # TODO: this counts characters, but identity data is stored with a
    # 1024-byte identifier limit, so a multibyte identifier is accepted here
    # and only fails once we try to write it. Check the byte length, together
    # with the same check for CSV uploads.
    user_ids = serializers.ListField(
        child=serializers.CharField(max_length=2000), min_length=1
    )
