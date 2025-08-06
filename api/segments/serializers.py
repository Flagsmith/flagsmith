from typing import Any

import structlog
from django.conf import settings
from django.db import transaction
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from metadata.serializers import MetadataSerializer, MetadataSerializerMixin
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule

logger = structlog.get_logger()

DictList = list[dict[str, Any]]


class ConditionSerializer(serializers.ModelSerializer[Condition]):
    delete = serializers.BooleanField(
        write_only=True,
        required=False,
    )

    class Meta:
        model = Condition
        fields = [
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

    def create(self, validated_data: dict[str, Any]) -> Condition:
        if self.context.get("is_creating_segment"):
            validated_data["created_with_segment"] = True
        return super().create(validated_data)


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
            "type",
            "rules",
            "conditions",
            "delete",
        ]


class SegmentSerializer(MetadataSerializerMixin, WritableNestedModelSerializer):
    rules = SegmentRuleSerializer(many=True, required=True, allow_empty=False)
    metadata = MetadataSerializer(required=False, many=True)

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
        ]

    def get_initial(self) -> dict[str, Any]:
        attrs: dict[str, Any] = super().get_initial()
        attrs["rules"] = self._get_rules_and_conditions_without_deleted(attrs["rules"])
        return attrs

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = super().validate(attrs)
        project = self.instance.project if self.instance else attrs["project"]  # type: ignore[union-attr]
        organisation = project.organisation
        self._validate_required_metadata(organisation, attrs.get("metadata", []))
        self._validate_segment_rules_conditions_limit(attrs["rules"])
        self._validate_project_segment_limit(project)
        return attrs

    def create(self, validated_data: dict[str, Any]):  # type: ignore[no-untyped-def]
        self.context["is_creating_segment"] = True
        metadata_data = validated_data.pop("metadata", [])
        segment = super().create(validated_data)  # type: ignore[no-untyped-call]
        self._update_metadata(segment, metadata_data)
        return segment

    def update(self, segment: Segment, validated_data: dict[str, Any]):  # type: ignore[no-untyped-def]
        metadata = validated_data.pop("metadata", [])
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
        return segment

    def _get_rules_and_conditions_without_deleted(
        self, rules_data: DictList
    ) -> DictList:
        """
        Remove rules and conditions marked for deletion from input

        NOTE: This is to support previous API design, in which any nested rules
        or conditions including both an `"id"` field and `"delete": true` were
        later soft-deleted in the database.

        TODO: Deprecate this in favor of not sending unwanted rules and
        conditions in the input.
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
        segment_count = Segment.live_objects.filter(project=project).count()
        if segment_count >= project.max_segments_allowed:
            raise ValidationError(
                {
                    "project": "The project has reached the maximum allowed segments limit."
                }
            )

    def _validate_segment_rules_conditions_limit(self, rules_data: DictList) -> None:
        if self.instance and getattr(self.instance, "whitelisted_segment", None):
            return

        def _count_conditions(rules_data: DictList) -> int:
            return sum(
                len(rule.get("conditions", []))
                + _count_conditions(rule.get("rules", []))
                for rule in rules_data
            )

        condition_count = _count_conditions(rules_data)
        if condition_count > settings.SEGMENT_RULES_CONDITIONS_LIMIT:
            raise ValidationError(
                {
                    "segment": f"The segment has {condition_count} conditions, which exceeds the maximum condition count of {settings.SEGMENT_RULES_CONDITIONS_LIMIT}."
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
