# -*- coding: utf-8 -*-
from django.db import models

from django.utils.encoding import python_2_unicode_compatible

# Condition Operation Value Types
EXACT_MATCH = "ExactMatch"
GREATER_THAN = "GreaterThan"
LESS_THAN = "LessThan"

@python_2_unicode_compatible
class Segment(models.Model):
    name = models.CharField(max_length=2000)
    description = models.TextField(null=True, blank=True)

@python_2_unicode_compatible
class SegmentCondition(models.Model):
    CONDITION_OPERATION_TYPES = (
        (EXACT_MATCH, 'ExactMatch'),
        (GREATER_THAN, 'GreaterThan'),
        (LESS_THAN, 'LessThan')
    )

    segment = models.ForeignKey(Segment, related_name='segment_conditions')
    trait_key = models.CharField(max_length=200)
    condition_type = models.CharField(max_length=20, choices=CONDITION_OPERATION_TYPES, default=EXACT_MATCH,
                            null=False, blank=False)
    match_value = models.TextField(null=True, blank=True)
    
