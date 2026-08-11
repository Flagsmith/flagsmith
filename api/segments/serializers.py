from typing import Any

import structlog
from django.db import transaction
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from edge_api.utils import is_edge_enabled
from metadata.serializers import MetadataSerializer, MetadataSerializerMixin
from projects.models import Project
from segment_membership.constants import MAX_SEGMENT_MEMBERS_PAGE_SIZE
from segment_membership.models import SegmentMembershipCount
from segment_membership.services import enqueue_membership_refresh
from segments.models import Condition, Segment, SegmentRule
from segments.types import LegacySegmentRule

# TODO: Delete alias as per https://github.com/Flagsmith/flagsmith/issues/7818
from segments.types import SegmentRule as SegmentRuleType
from segments.validators import SegmentRulesValidator

logger = structlog.get_logger(__name__)

DictList = list[dict[str, Any]]


class SegmentMembershipCountSerializer(
    serializers.ModelSerializer[SegmentMembershipCount]
):
    class Meta:
        model = SegmentMembershipCount
        fields = ["environment", "count", "last_synced_at"]
        read_only_fields = ["environment", "count", "last_synced_at"]


class ConditionSerializer(serializers.ModelSerializer[Condition]):
    delete = serializers.BooleanField(
        write_only=True,
        required=False,
    )

    class Meta:
        model = Condition
        fields = [
            "id",
            "operator",
            "property",
            "value",
            "description",
            "delete",
        ]

    def to_internal_value(self, data: dict[str, Any]) -> Any:
        # Conversion to correct value type is handled elsewhere
        data["value"] = str(data["value"]) if "value" in data else None
        return super().to_internal_value(data)


class _BaseSegmentRuleSerializer(WritableNestedModelSerializer):
    delete = serializers.BooleanField(
        write_only=True,
        required=False,
    )
    conditions = ConditionSerializer(
        many=True,
        required=False,
    )


class _NestedSegmentRuleSerializer(_BaseSegmentRuleSerializer):
    class Meta:
        model = SegmentRule
        fields = [
            "id",
            "type",
            "conditions",
            "delete",
        ]


class SegmentRuleSerializer(_BaseSegmentRuleSerializer):
    rules = _NestedSegmentRuleSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = SegmentRule
        fields = [
            "id",
            "type",
            "rules",
            "conditions",
            "delete",
        ]


class SegmentSerializer(MetadataSerializerMixin, WritableNestedModelSerializer):
    rules = SegmentRuleSerializer(many=True, required=True, allow_empty=False)
    metadata = MetadataSerializer(required=False, many=True)
    membership_counts = SegmentMembershipCountSerializer(many=True, read_only=True)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Because WritableNestedModelSerializer uses `initial_data` instead of `data`
        we need to override the `__init__` method to remove rules and conditions
        that are marked for deletion.

        TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
        """
        data = kwargs.get("data")
        if data and "rules" in data:
            data["rules"] = self._get_rules_and_conditions_without_deleted(
                data["rules"]
            )
            kwargs["data"] = data

        super().__init__(*args, **kwargs)

    class Meta:
        model = Segment
        fields = [
            "id",
            "uuid",
            "created_at",
            "updated_at",
            "name",
            "description",
            "project",
            "feature",
            "version_of",
            "rules",
            "metadata",
            "membership_counts",
        ]
        read_only_fields = [
            "membership_counts",
            "project",
            "version_of",
        ]
        validators = [SegmentRulesValidator()]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = super().validate(attrs)
        metadata = attrs.get("metadata", [])

        # TODO: Make "project" read-only — https://github.com/Flagsmith/flagsmith-workflows/issues/102
        project_pk = self.context["view"].kwargs["project_pk"]
        project = attrs["project"] = Project.objects.get(pk=project_pk)
        organisation = project.organisation

        self._validate_required_metadata(organisation, metadata, project)
        self._validate_project_segment_limit(project)
        return attrs

    def create(self, validated_data: dict[str, Any]):  # type: ignore[no-untyped-def]
        metadata_data = validated_data.pop("metadata", [])
        self._set_rules_data(validated_data)
        segment = super().create(validated_data)  # type: ignore[no-untyped-call]
        self._update_metadata(segment, metadata_data)
        enqueue_membership_refresh(segment.project)
        return segment

    def update(self, segment: Segment, validated_data: dict[str, Any]):  # type: ignore[no-untyped-def]
        metadata = validated_data.pop("metadata", [])
        self._set_rules_data(validated_data)
        with transaction.atomic():
            if not segment.change_request:
                segment_revision = segment.clone(is_revision=True)
                logger.info(
                    "segment-revision-created",
                    segment_id=segment.id,
                    revision_id=segment_revision.id,
                )
            segment = super().update(segment, validated_data)  # type: ignore[no-untyped-call]
        self._update_metadata(segment, metadata)
        enqueue_membership_refresh(segment.project)
        return segment

    def _set_rules_data(self, validated_data: dict[str, Any]) -> None:
        """Set the .rules_data attribute
        TODO: Delete this as per https://github.com/Flagsmith/flagsmith/issues/7818
        """
        if "rules" not in validated_data:
            return  # PATCH support
        validated_data["rules_data"] = self._cleanup_rules_and_conditions(
            validated_data["rules"]
        )

    def _cleanup_rules_and_conditions(
        self, rules_data: list[LegacySegmentRule]
    ) -> list[SegmentRuleType]:
        """Remove any `id` fields and `delete: true` items from rules and conditions

        In https://github.com/Flagsmith/flagsmith/issues/7814, we moved from a
        SegmentRule and Condition tree to a JSON field. This cleanup exists to
        keep the interface compatible."""
        return [
            {
                "type": rule_data["type"],
                "conditions": [
                    {
                        "property": condition_data["property"],
                        "operator": condition_data["operator"],
                        "value": condition_data.get("value"),
                        "description": condition_data.get("description"),
                    }
                    for condition_data in rule_data.get("conditions", [])
                    if not condition_data.get("delete")
                ],
                "rules": self._cleanup_rules_and_conditions(rule_data.get("rules", [])),
            }
            for rule_data in rules_data
            if not rule_data.get("delete")
        ]

    def _get_rules_and_conditions_without_deleted(
        self, rules_data: DictList
    ) -> DictList:
        """
        Remove rules and conditions marked for deletion from input

        NOTE: This is to support previous API design, in which any nested rules
        or conditions including both an `"id"` field and `"delete": true` were
        later soft-deleted in the database.

        TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
        """
        return [
            {
                **rule_data,
                "conditions": [
                    condition_data
                    for condition_data in rule_data.get("conditions", [])
                    if not condition_data.get("delete")
                ],
                "rules": self._get_rules_and_conditions_without_deleted(
                    rule_data.get("rules", [])
                ),
            }
            for rule_data in rules_data
            if not rule_data.get("delete")
        ]

    def _validate_project_segment_limit(self, project: Project) -> None:
        if not is_edge_enabled():
            return
        segment_count = Segment.live_objects.filter(project=project).count()
        if segment_count >= project.max_segments_allowed:
            raise ValidationError(
                {
                    "project": "The project has reached the maximum allowed segments limit."
                }
            )


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


class CloneSegmentSerializer(serializers.ModelSerializer[Segment]):
    class Meta:
        model = Segment
        fields = ("name",)


class SegmentMembersQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    environment = serializers.IntegerField(
        help_text="The id of the environment to list segment members for.",
    )
    cursor = serializers.CharField(
        required=False,
        help_text="The identifier of the previous page's last row; omit for the first page.",
    )
    q = serializers.CharField(
        required=False,
        help_text="Case-insensitive substring to filter members by identifier.",
    )
    limit = serializers.IntegerField(
        required=False,
        default=100,
        min_value=1,
        max_value=MAX_SEGMENT_MEMBERS_PAGE_SIZE,
        help_text=f"Page size, up to {MAX_SEGMENT_MEMBERS_PAGE_SIZE}.",
    )


class SegmentMemberSerializer(serializers.Serializer):  # type: ignore[type-arg]
    identifier = serializers.CharField()
    identity_key = serializers.CharField()
    traits = serializers.JSONField()


class SegmentMembersResponseSerializer(serializers.Serializer):  # type: ignore[type-arg]
    results = SegmentMemberSerializer(many=True)
    next_cursor = serializers.CharField(
        allow_null=True,
        help_text="Pass as `cursor` to fetch the next page; null when there are no more rows.",
    )
