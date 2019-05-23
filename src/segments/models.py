# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.db import models

from django.utils.encoding import python_2_unicode_compatible

from projects.models import Project


@python_2_unicode_compatible
class Segment(models.Model):
    name = models.CharField(max_length=2000)
    description = models.TextField(null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="segments")

    def __str__(self):
        return "Segment - %s" % self.name


@python_2_unicode_compatible
class SegmentRule(models.Model):
    ALL_RULE = "ALL"
    ANY_RULE = "ANY"
    NONE_RULE = "NONE"

    RULE_TYPES = (
        (ALL_RULE, "all"),
        (ANY_RULE, "any"),
        (NONE_RULE, "none")
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
        return "rule %d" % self.id


@python_2_unicode_compatible
class Condition(models.Model):
    EQUAL = "EQUAL"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"

    CONDITION_TYPES = (
        (EQUAL, "Exactly Equal"),
        (GREATER_THAN, "Greater than"),
        (LESS_THAN, "Less than")
    )

    operator = models.CharField(choices=CONDITION_TYPES, max_length=500)
    property = models.CharField(max_length=1000)
    value = models.CharField(max_length=1000)

    rule = models.ForeignKey(SegmentRule, on_delete=models.CASCADE, related_name="conditions")

    def __str__(self):
        return "Condition %d: %s %s %s" % (self.id, self.property, self.operator, self.value)
