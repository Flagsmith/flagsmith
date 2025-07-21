import logging
from typing import Any

from common.metadata.serializers import (
    MetadataSerializer,
    SerializerWithMetadata,
)
from django.conf import settings
from django.db.models.functions import Coalesce
from drf_writable_nested.serializers import WritableNestedModelSerializer
from flag_engine.segments.constants import PERCENTAGE_SPLIT
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_recursive.fields import (  # type: ignore[import-untyped]
    RecursiveField,
)

from projects.models import Project
from segments.models import Condition, Segment, SegmentRule

logger = logging.getLogger(__name__)

DictList = list[dict[str, Any]]


class ConditionSerializer(serializers.ModelSerializer[Condition]):
    id = serializers.IntegerField(
        read_only=False,
        required=False,
    )
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
        attrs = super().validate(attrs)
        if attrs.get("operator") != PERCENTAGE_SPLIT and not attrs.get("property"):
            raise ValidationError({"property": ["This field may not be blank."]})
        return attrs

    def to_internal_value(self, data: dict[str, Any]) -> Any:
        # Conversion to correct value type is handled elsewhere
        data["value"] = str(data["value"]) if "value" in data else None
        return super().to_internal_value(data)

    def create(self, validated_data: dict[str, Any]) -> Condition:
        if self.context.get("is_creating_segment"):
            validated_data["created_with_segment"] = True
        return super().create(validated_data)


class _BaseSegmentRuleSerializer(WritableNestedModelSerializer):
    id = serializers.IntegerField(
        read_only=False,
        required=False,
    )
    delete = serializers.BooleanField(
        write_only=True,
        required=False,
    )
    conditions = ConditionSerializer(
        many=True,
        required=False,
    )
    version_of = RecursiveField(
        required=False,
        allow_null=True,
    )


class _NestedSegmentRuleSerializer(_BaseSegmentRuleSerializer):
    class Meta:
        model = SegmentRule
        fields = [
            "id",
            "type",
            "conditions",
            "delete",
            "version_of",
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
            "version_of",
        ]


class SegmentSerializer(WritableNestedModelSerializer, SerializerWithMetadata):
    rules = SegmentRuleSerializer(
        many=True,
    )
    metadata = MetadataSerializer(
        required=False,
        many=True,
    )

    class Meta:
        model = Segment
        fields = "__all__"

    def get_initial(self) -> dict[str, Any]:
        initial_data: dict[str, Any] = super().get_initial()
        if rules_data := initial_data.get("rules"):
            self._remove_segment_rules_conditions_marked_for_deletion(rules_data)
        return initial_data

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = super().validate(attrs)
        if not attrs.get("rules"):
            raise ValidationError(
                {"rules": "Segment cannot be created without any rules."}
            )
        self.validate_required_metadata(attrs)
        self._validate_segment_rules_conditions_limit(attrs["rules"])
        self._validate_relations_of_nested_rules_and_conditions(attrs["rules"])
        return attrs

    # Needed by SerializerWithMetadata.get_organisation
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
        self._validate_project_segment_limit(project)

        metadata_data = validated_data.pop("metadata", [])

        self.context["is_creating_segment"] = True
        segment: Segment = super().create(validated_data)  # type: ignore[no-untyped-call]

        self.update_metadata(segment, metadata_data)

        return segment

    def update(
        self,
        instance: Segment,
        validated_data: dict[str, Any],
    ) -> Segment:
        metadata_data = validated_data.pop("metadata", [])

        # Create a version of the segment now that we're updating.
        cloned_segment = instance.deep_clone()
        logger.info(
            f"Updating cloned segment {cloned_segment.id} for original segment {instance.id}"
        )

        try:
            self.update_metadata(instance, metadata_data)
            instance = super().update(instance, validated_data)  # type: ignore[no-untyped-call]
        except Exception:
            # Roll back ¯\_(ツ)_/¯
            instance.refresh_from_db()
            instance.version = cloned_segment.version
            instance.save()
            cloned_segment.hard_delete()
            raise

        return instance

    def _validate_relations_of_nested_rules_and_conditions(  # noqa: C901
        self, rules_data: DictList
    ) -> None:
        """
        Check whether every rule and condition is associated with the segment
        """

        def collect_ids(rules_data: DictList) -> None:
            for rule_data in rules_data:
                if rule_id := rule_data.get("id"):
                    rules_ids.add(rule_id)
                for condition_data in rule_data.get("conditions", []):
                    if condition_id := condition_data.get("id"):
                        rule_condition_ids.add((rule_id, condition_id))
                collect_ids(rule_data.get("rules", []))

        rules_ids: set[int] = set()
        rule_condition_ids: set[tuple[int | None, int]] = set()
        collect_ids(rules_data)
        condition_ids = {condition_id for _, condition_id in rule_condition_ids}

        if not self.instance:
            # A new segment can never receive any existing rule or condition
            if rules_ids or rule_condition_ids:
                raise ValidationError({"segment": "Mismatched segment is not allowed"})
            return

        # Edge case but saves energy <3
        if None in (rule_id for rule_id, _ in rule_condition_ids):
            raise ValidationError({"segment": "Cannot move conditions between rules"})

        # Replacing all rules is OK
        if not (rules_ids or condition_ids):
            return

        segments_from_rules = set(
            SegmentRule.objects.annotate(
                actual_segment_id=Coalesce(
                    "segment_id",
                    "rule__segment_id",
                ),
            )
            .filter(pk__in=rules_ids)
            .values_list("actual_segment_id", flat=True)
        )

        # Ensure this is the only segment associated with the rules
        if segments_from_rules != {self.instance.pk}:  # type: ignore[union-attr]
            raise ValidationError({"segment": "Mismatched segment is not allowed"})

        existing_rule_conditions_ids = set(
            Condition.objects.filter(
                pk__in=condition_ids,
            ).values_list("rule_id", "id")
        )

        # Ensure existing conditions continue belonging to their rules
        if not rule_condition_ids <= existing_rule_conditions_ids:
            raise ValidationError({"segment": "Cannot move conditions between rules"})

    def _remove_segment_rules_conditions_marked_for_deletion(
        self,
        rules_data: DictList,
    ) -> None:
        """
        Remove rules and conditions marked for deletion from input

        NOTE: This is to support previous API design, in which any nested rules
        or conditions including both an `"id"` field and `"delete": true` were
        later soft-deleted in the database.

        TODO: Deprecate this in favor of not sending unwanted rules and
        conditions in the input.
        """
        for r in range(len(rules_data)):
            if (rule := rules_data[r]).get("delete") is True:
                del rules_data[r]
                continue
            for c in range(len(conditions := rule.get("conditions", []))):
                if conditions[c].get("delete") is True:
                    del conditions[c]
            if subrules := rule.get("rules", []):
                self._remove_segment_rules_conditions_marked_for_deletion(subrules)

    def _validate_project_segment_limit(self, project: Project) -> None:
        segment_count = Segment.live_objects.filter(project=project).count()
        if segment_count >= project.max_segments_allowed:
            msg = "The project has reached the maximum allowed segments limit."
            raise ValidationError({"project": msg})

    def _validate_segment_rules_conditions_limit(
        self,
        rules_data: DictList,
    ) -> None:
        if self.instance and getattr(self.instance, "whitelisted_segment", None):
            return

        condition_count = self._calculate_condition_count(rules_data)
        if condition_count > settings.SEGMENT_RULES_CONDITIONS_LIMIT:
            msg = (
                f"The segment has {condition_count} conditions, which exceeds the maximum "
                f"condition count of {settings.SEGMENT_RULES_CONDITIONS_LIMIT}."
            )
            raise ValidationError({"segment": msg})

    def _calculate_condition_count(
        self,
        rules_data: DictList,
    ) -> int:
        count = 0
        for rule_data in rules_data:
            child_rules: DictList = rule_data.get("rules", [])
            if child_rules:
                count += self._calculate_condition_count(child_rules)
            conditions: DictList = rule_data.get("conditions", [])
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
