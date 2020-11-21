from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ListSerializer
from rest_framework_recursive.fields import RecursiveField

from audit.models import (
    SEGMENT_CREATED_MESSAGE,
    SEGMENT_UPDATED_MESSAGE,
    AuditLog,
    RelatedObjectType,
)
from segments.models import Condition, Segment, SegmentRule

from . import models


class ConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Condition
        fields = ("operator", "property", "value")

    def validate(self, attrs):
        super(ConditionSerializer, self).validate(attrs)
        if attrs.get("operator") != models.PERCENTAGE_SPLIT and not attrs.get(
            "property"
        ):
            raise ValidationError({"property": ["This field may not be blank."]})
        return attrs

    def to_internal_value(self, data):
        # convert value to a string - conversion to correct value type is handled elsewhere
        data["value"] = str(data["value"])
        return super(ConditionSerializer, self).to_internal_value(data)


class RuleSerializer(serializers.ModelSerializer):
    conditions = ConditionSerializer(many=True, required=False)
    rules = ListSerializer(child=RecursiveField(), required=False)

    class Meta:
        model = models.SegmentRule
        fields = ("type", "rules", "conditions")


class SegmentSerializer(serializers.ModelSerializer):
    rules = RuleSerializer(many=True)

    class Meta:
        model = models.Segment
        fields = "__all__"

    def validate(self, attrs):
        if not attrs.get("rules"):
            raise ValidationError(
                {"rules": "Segment cannot be created without any rules."}
            )
        return attrs

    def create(self, validated_data):
        """
        Override create method to create segment with nested rules and conditions

        :param validated_data: validated json data
        :return: created Segment object
        """
        rules_data = validated_data.pop("rules", [])
        segment = Segment.objects.create(**validated_data)
        self._create_segment_rules(rules_data, segment=segment)
        self._create_audit_log(segment, True)
        return segment

    def update(self, instance, validated_data):
        rules_data = validated_data.pop("rules", [])
        self._update_segment_rules(rules_data, segment=instance)
        self._create_audit_log(instance, False)
        return super().update(instance, validated_data)

    def _update_segment_rules(self, rules_data, segment=None):
        """
        Since we don't have a unique identifier for the rules / conditions for the update, we assume that the client
        passes up the new configuration for the rules of the segment and simply wipe the old ones and create new ones
        """
        segment.rules.set([])
        self._create_segment_rules(rules_data, segment=segment)
        segment.save()

    def _create_segment_rules(self, rules_data, segment=None, rule=None):
        if all(x is None for x in {segment, rule}):
            raise RuntimeError("Can't create rule without parent segment or rule")

        for rule_data in rules_data:
            child_rules = rule_data.pop("rules", [])
            conditions = rule_data.pop("conditions", [])

            child_rule = self._create_segment_rule(rule_data, segment, rule)

            self._create_conditions(conditions, child_rule)

            self._create_segment_rules(child_rules, rule=child_rule)

    @staticmethod
    def _create_segment_rule(rule_data, segment, rule):
        if segment:
            segment_rule = SegmentRule.objects.create(segment=segment, **rule_data)
        else:
            segment_rule = SegmentRule.objects.create(rule=rule, **rule_data)

        return segment_rule

    @staticmethod
    def _create_conditions(conditions_data, rule):
        for condition in conditions_data:
            Condition.objects.create(rule=rule, **condition)

    def _create_audit_log(self, instance, created):
        message = (
            SEGMENT_CREATED_MESSAGE % instance.name
            if created
            else SEGMENT_UPDATED_MESSAGE % instance.name
        )
        request = self.context.get("request")
        AuditLog.objects.create(
            author=request.user if request else None,
            related_object_id=instance.id,
            related_object_type=RelatedObjectType.SEGMENT.name,
            project=instance.project,
            log=message,
        )


class SegmentSerializerBasic(serializers.ModelSerializer):
    class Meta:
        model = Segment
        fields = ("id", "name", "description")
