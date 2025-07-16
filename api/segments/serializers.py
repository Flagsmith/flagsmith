import logging
from typing import Any

from common.metadata.serializers import (
    MetadataSerializer,
    SerializerWithMetadata,
)
from django.conf import settings
from flag_engine.segments.constants import PERCENTAGE_SPLIT
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ListSerializer
from rest_framework_recursive.fields import (  # type: ignore[import-untyped]
    RecursiveField,
)

from projects.models import Project
from segments.models import Condition, Segment, SegmentRule

logger = logging.getLogger(__name__)


class ConditionSerializer(serializers.ModelSerializer[Condition]):
    delete = serializers.BooleanField(
        write_only=True,
        required=False,
    )
    version_of = RecursiveField(
        required=False,
        allow_null=True,
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
            "version_of",
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        super().validate(attrs)
        if attrs.get("operator") != PERCENTAGE_SPLIT and not attrs.get("property"):
            raise ValidationError({"property": ["This field may not be blank."]})
        return attrs

    def to_internal_value(self, data: dict[str, Any]) -> Any:
        # Conversion to correct value type is handled elsewhere
        data["value"] = str(data["value"]) if "value" in data else None
        return super().to_internal_value(data)


# TODO: Rename to SegmentRuleSerializer
class RuleSerializer(serializers.ModelSerializer[SegmentRule]):
    delete = serializers.BooleanField(
        write_only=True,
        required=False,
    )
    conditions = ConditionSerializer(
        many=True,
        required=False,
    )
    rules: ListSerializer[SegmentRule] = ListSerializer(
        child=RecursiveField(),
        required=False,
    )
    version_of = RecursiveField(
        required=False,
        allow_null=True,
    )

    class Meta:
        model = SegmentRule
        fields = [
            "id",
            "type",
            "rules",
            "conditions",
            "delete",
            "version_of",
        ]


class SegmentSerializer(serializers.ModelSerializer[Segment], SerializerWithMetadata):
    rules = RuleSerializer(
        many=True,
    )
    metadata = MetadataSerializer(
        required=False,
        many=True,
    )

    class Meta:
        model = Segment
        fields = "__all__"

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = super().validate(attrs)
        self.validate_required_metadata(attrs)
        if not attrs.get("rules"):
            raise ValidationError(
                {"rules": "Segment cannot be created without any rules."}
            )
        return attrs

    def get_project(
        self,
        validated_data: dict[str, Any] | None = None,
    ) -> Project:
        project: Project
        if validated_data and "project" in validated_data:
            project = validated_data["project"]
            return project
        project = Project.objects.get(id=self.context["view"].kwargs["project_pk"])
        return project

    def create(self, validated_data: dict[str, Any]) -> Segment:
        project = validated_data["project"]
        self.validate_project_segment_limit(project)

        rules_data = validated_data.pop("rules", [])
        metadata_data = validated_data.pop("metadata", [])
        self.validate_segment_rules_conditions_limit(rules_data)

        # create segment with nested rules and conditions
        segment: Segment = Segment.objects.create(**validated_data)
        self.update_metadata(segment, metadata_data)
        segment.refresh_from_db()
        return segment

    def update(
        self,
        instance: Segment,
        validated_data: dict[str, Any],
    ) -> Segment:
        # use the initial data since we need the ids included to determine which to update & which to create
        rules_data = self.initial_data.pop("rules", [])
        metadata_data = validated_data.pop("metadata", [])
        self.validate_segment_rules_conditions_limit(rules_data)

        # Create a version of the segment now that we're updating.
        cloned_segment = instance.deep_clone()
        logger.info(
            f"Updating cloned segment {cloned_segment.id} for original segment {instance.id}"
        )

        try:
            self.update_metadata(instance, metadata_data)

            # remove rules from validated data to prevent error trying to create segment with nested rules
            del validated_data["rules"]
            instance = super().update(instance, validated_data)
        except Exception:
            # Roll back ¯\_(ツ)_/¯
            instance.refresh_from_db()
            instance.version = cloned_segment.version
            instance.save()
            cloned_segment.hard_delete()
            raise

        return instance

    def validate_project_segment_limit(self, project: Project) -> None:
        if (
            Segment.live_objects.filter(project=project).count()
            >= project.max_segments_allowed
        ):
            raise ValidationError(
                {
                    "project": "The project has reached the maximum allowed segments limit.",
                }
            )

    def validate_segment_rules_conditions_limit(
        self,
        rules_data: list[dict[str, Any]],
    ) -> None:
        if self.instance and getattr(self.instance, "whitelisted_segment", None):
            return

        count = self._calculate_condition_count(rules_data)

        if count > settings.SEGMENT_RULES_CONDITIONS_LIMIT:
            raise ValidationError(
                {
                    "segment": (
                        f"The segment has {count} conditions, which exceeds the maximum "
                        f"condition count of {settings.SEGMENT_RULES_CONDITIONS_LIMIT}."
                    )
                }
            )

    def _calculate_condition_count(
        self,
        rules_data: list[dict[str, Any]],
    ) -> int:
        count: int = 0

        for rule_data in rules_data:
            child_rules: list[dict[str, Any]] = rule_data.get("rules", [])
            if child_rules:
                count += self._calculate_condition_count(child_rules)
            conditions: list[dict[str, Any]] = rule_data.get("conditions", [])
            for condition in conditions:
                if condition.get("delete", False) is True:
                    continue
                count += 1
        return count


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
