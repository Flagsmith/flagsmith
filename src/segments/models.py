# -*- coding: utf-8 -*-
import re
import sys
import hashlib

from django.core.exceptions import ValidationError
from django.db import models

from django.utils.encoding import python_2_unicode_compatible

from environments.models import Identity, INTEGER, BOOLEAN
from projects.models import Project


# Condition Types
EQUAL = "EQUAL"
GREATER_THAN = "GREATER_THAN"
LESS_THAN = "LESS_THAN"
LESS_THAN_INCLUSIVE = "LESS_THAN_INCLUSIVE"
CONTAINS = "CONTAINS"
GREATER_THAN_INCLUSIVE = "GREATER_THAN_INCLUSIVE"
NOT_CONTAINS = "NOT_CONTAINS"
NOT_EQUAL = "NOT_EQUAL"
REGEX = "REGEX"


@python_2_unicode_compatible
class Segment(models.Model):
    name = models.CharField(max_length=2000)
    description = models.TextField(null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="segments")

    def __str__(self):
        return "Segment - %s" % self.name

    def does_identity_match(self, identity: Identity) -> bool:
        return all(rule.does_identity_match(identity) for rule in self.rules.all())


@python_2_unicode_compatible
class SegmentRule(models.Model):
    ALL_RULE = "ALL"
    ANY_RULE = "ANY"
    NONE_RULE = "NONE"
    PERCENTAGE_SPLIT = "PERCENTAGE_SPLIT"

    RULE_TYPES = (
        (ALL_RULE, "all"),
        (ANY_RULE, "any"),
        (NONE_RULE, "none"),
        (PERCENTAGE_SPLIT, "Percentage split")
    )

    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name="rules", null=True, blank=True)
    rule = models.ForeignKey('self', on_delete=models.CASCADE, related_name="rules", null=True, blank=True)

    type = models.CharField(max_length=50, choices=RULE_TYPES)

    def clean(self):
        super().clean()
        parents = [self.segment, self.rule]
        num_parents = sum(parent is not None for parent in parents)
        if num_parents != 1:
            raise ValidationError("Segment rule must have exactly one parent, %d found", num_parents)

    def __str__(self):
        return "%s rule for %s" % (self.type, str(self.segment) if self.segment else str(self.rule))

    def does_identity_match(self, identity: Identity) -> bool:
        matches_conditions = False

        if self.conditions.count() == 0:
            matches_conditions = True
        elif self.type == self.ALL_RULE:
            matches_conditions = all(condition.does_identity_match(identity) for condition in self.conditions.all())
        elif self.type == self.ANY_RULE:
            matches_conditions = any(condition.does_identity_match(identity) for condition in self.conditions.all())
        elif self.type == self.NONE_RULE:
            matches_conditions = not any(condition.does_identity_match(identity) for condition in self.conditions.all())

        return matches_conditions and all(rule.does_identity_match(identity) for rule in self.rules.all())

    def get_identity_percentage_value(self, identity: Identity) -> float:
        """
        Given a segment and an identity, generate a number between 0 and 1 to determine whether the identity falls
        within a given percentile when using percentage split rules.
        """
        to_hash = f'{self.segment.id},{identity.id}'
        hashed_value = hashlib.md5(to_hash.encode('utf-8'))
        hashed_value_as_int = int(hashed_value.hexdigest(), base=16)
        return (hashed_value_as_int % 9999) / 9998


@python_2_unicode_compatible
class Condition(models.Model):
    CONDITION_TYPES = (
        (EQUAL, "Exactly Matches"),
        (GREATER_THAN, "Greater than"),
        (LESS_THAN, "Less than"),
        (CONTAINS, "Contains"),
        (GREATER_THAN_INCLUSIVE, "Greater than or equal to"),
        (LESS_THAN_INCLUSIVE, "Less than or equal to"),
        (NOT_CONTAINS, "Does not contain"),
        (NOT_EQUAL, "Does not match"),
        (REGEX, "Matches regex")
    )

    operator = models.CharField(choices=CONDITION_TYPES, max_length=500)
    property = models.CharField(max_length=1000)
    value = models.CharField(max_length=1000)

    rule = models.ForeignKey(SegmentRule, on_delete=models.CASCADE, related_name="conditions")

    def __str__(self):
        return "Condition for %s: %s %s %s" % (str(self.rule), self.property, self.operator, self.value)

    def does_identity_match(self, identity: Identity) -> bool:
        for trait in identity.identity_traits.all():
            if trait.trait_key == self.property:
                if trait.value_type == INTEGER:
                    return self.check_integer_value(trait.integer_value)
                elif trait.value_type == BOOLEAN:
                    return self.check_boolean_value(trait.boolean_value)
                else:
                    return self.check_string_value(trait.string_value)

    def check_integer_value(self, value: int) -> bool:
        try:
            int_value = int(str(self.value))
        except ValueError:
            return False

        if self.operator == EQUAL:
            return value == int_value
        elif self.operator == GREATER_THAN:
            return value > int_value
        elif self.operator == GREATER_THAN_INCLUSIVE:
            return value >= int_value
        elif self.operator == LESS_THAN:
            return value < int_value
        elif self.operator == LESS_THAN_INCLUSIVE:
            return value <= int_value
        elif self.operator == NOT_EQUAL:
            return value != int_value

        return False

    def check_boolean_value(self, value: bool) -> bool:
        if self.value in ('False', 'false', '0'):
            bool_value = False
        elif self.value in ('True', 'true', '1'):
            bool_value = True
        else:
            return False

        if self.operator == EQUAL:
            return value == bool_value
        elif self.operator == NOT_EQUAL:
            return value != bool_value

        return False

    def check_string_value(self, value: str) -> bool:
        try:
            str_value = str(self.value)
        except ValueError:
            return False

        if self.operator == EQUAL:
            return value == str_value
        elif self.operator == NOT_EQUAL:
            return value != str_value
        elif self.operator == CONTAINS:
            return str_value in value
        elif self.operator == NOT_CONTAINS:
            return str_value not in value
        elif self.operator == REGEX:
            return re.compile(str(self.value)).match(value) is not None
