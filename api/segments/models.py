import logging
import typing

import semver
from core.constants import BOOLEAN, FLOAT, INTEGER
from core.models import AbstractBaseExportableModel
from django.core.exceptions import ValidationError
from django.db import models
from flag_engine.utils.semver import is_semver, remove_semver_suffix

from environments.identities.helpers import (
    get_hashed_percentage_for_object_ids,
)
from projects.models import Project

if typing.TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait


logger = logging.getLogger(__name__)

try:
    import re2 as re

    logger.info("Using re2 library for regex.")
except ImportError:
    logger.warning("Unable to import re2. Falling back to re.")
    import re

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
PERCENTAGE_SPLIT = "PERCENTAGE_SPLIT"


class Segment(AbstractBaseExportableModel):
    name = models.CharField(max_length=2000)
    description = models.TextField(null=True, blank=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="segments"
    )

    class Meta:
        ordering = ("id",)  # explicit ordering to prevent pagination warnings

    def __str__(self):
        return "Segment - %s" % self.name

    def does_identity_match(
        self, identity: "Identity", traits: typing.List["Trait"] = None
    ) -> bool:
        rules = self.rules.all()
        return rules.count() > 0 and all(
            rule.does_identity_match(identity, traits) for rule in rules
        )


class SegmentRule(AbstractBaseExportableModel):
    ALL_RULE = "ALL"
    ANY_RULE = "ANY"
    NONE_RULE = "NONE"

    RULE_TYPES = ((ALL_RULE, "all"), (ANY_RULE, "any"), (NONE_RULE, "none"))

    segment = models.ForeignKey(
        Segment, on_delete=models.CASCADE, related_name="rules", null=True, blank=True
    )
    rule = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="rules", null=True, blank=True
    )

    type = models.CharField(max_length=50, choices=RULE_TYPES)

    def clean(self):
        super().clean()
        parents = [self.segment, self.rule]
        num_parents = sum(parent is not None for parent in parents)
        if num_parents != 1:
            raise ValidationError(
                "Segment rule must have exactly one parent, %d found", num_parents
            )

    def __str__(self):
        return "%s rule for %s" % (
            self.type,
            str(self.segment) if self.segment else str(self.rule),
        )

    def does_identity_match(
        self, identity: "Identity", traits: typing.List["Trait"] = None
    ) -> bool:
        matches_conditions = False
        conditions = self.conditions.all()

        if conditions.count() == 0:
            matches_conditions = True
        elif self.type == self.ALL_RULE:
            matches_conditions = all(
                condition.does_identity_match(identity, traits)
                for condition in conditions
            )
        elif self.type == self.ANY_RULE:
            matches_conditions = any(
                condition.does_identity_match(identity, traits)
                for condition in conditions
            )
        elif self.type == self.NONE_RULE:
            matches_conditions = not any(
                condition.does_identity_match(identity, traits)
                for condition in conditions
            )

        return matches_conditions and all(
            rule.does_identity_match(identity, traits) for rule in self.rules.all()
        )

    def get_segment(self):
        """
        rules can be a child of a parent rule instead of a segment, this method iterates back up the tree to find the
        segment

        TODO: denormalise the segment information so that we don't have to make multiple queries here in complex cases
        """
        rule = self
        while not rule.segment:
            rule = rule.rule
        return rule.segment


class Condition(AbstractBaseExportableModel):
    CONDITION_TYPES = (
        (EQUAL, "Exactly Matches"),
        (GREATER_THAN, "Greater than"),
        (LESS_THAN, "Less than"),
        (CONTAINS, "Contains"),
        (GREATER_THAN_INCLUSIVE, "Greater than or equal to"),
        (LESS_THAN_INCLUSIVE, "Less than or equal to"),
        (NOT_CONTAINS, "Does not contain"),
        (NOT_EQUAL, "Does not match"),
        (REGEX, "Matches regex"),
        (PERCENTAGE_SPLIT, "Percentage split"),
    )

    operator = models.CharField(choices=CONDITION_TYPES, max_length=500)
    property = models.CharField(blank=True, null=True, max_length=1000)
    value = models.CharField(max_length=1000)

    rule = models.ForeignKey(
        SegmentRule, on_delete=models.CASCADE, related_name="conditions"
    )

    def __str__(self):
        return "Condition for %s: %s %s %s" % (
            str(self.rule),
            self.property,
            self.operator,
            self.value,
        )

    def does_identity_match(
        self, identity: "Identity", traits: typing.List["Trait"] = None
    ) -> bool:
        if self.operator == PERCENTAGE_SPLIT:
            return self._check_percentage_split_operator(identity)

        # we allow passing in traits to handle when they aren't
        # persisted for certain organisations
        traits = identity.identity_traits.all() if traits is None else traits

        for trait in traits:
            if trait.trait_key == self.property:
                if trait.value_type == INTEGER:
                    return self.check_integer_value(trait.integer_value)
                if trait.value_type == FLOAT:
                    return self.check_float_value(trait.float_value)
                elif trait.value_type == BOOLEAN:
                    return self.check_boolean_value(trait.boolean_value)
                elif is_semver(self.value):
                    return self.check_semver_value(trait.string_value)
                else:
                    return self.check_string_value(trait.string_value)

    def _check_percentage_split_operator(self, identity):
        try:
            float_value = float(self.value) / 100.0
        except ValueError:
            return False

        segment = self.rule.get_segment()
        return (
            get_hashed_percentage_for_object_ids(object_ids=[segment.id, identity.id])
            <= float_value
        )

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

    def check_float_value(self, value: float) -> bool:
        try:
            float_value = float(str(self.value))
        except ValueError:
            return False

        if self.operator == EQUAL:
            return value == float_value
        elif self.operator == GREATER_THAN:
            return value > float_value
        elif self.operator == GREATER_THAN_INCLUSIVE:
            return value >= float_value
        elif self.operator == LESS_THAN:
            return value < float_value
        elif self.operator == LESS_THAN_INCLUSIVE:
            return value <= float_value
        elif self.operator == NOT_EQUAL:
            return value != float_value

        return False

    def check_boolean_value(self, value: bool) -> bool:
        if self.value in ("False", "false", "0"):
            bool_value = False
        elif self.value in ("True", "true", "1"):
            bool_value = True
        else:
            return False

        if self.operator == EQUAL:
            return value == bool_value
        elif self.operator == NOT_EQUAL:
            return value != bool_value

        return False

    def check_semver_value(self, value: str) -> bool:
        try:
            condition_version_info = semver.VersionInfo.parse(
                remove_semver_suffix(self.value)
            )
        except ValueError:
            return False

        if self.operator == EQUAL:
            return value == condition_version_info
        elif self.operator == GREATER_THAN:
            return value > condition_version_info
        elif self.operator == GREATER_THAN_INCLUSIVE:
            return value >= condition_version_info
        elif self.operator == LESS_THAN:
            return value < condition_version_info
        elif self.operator == LESS_THAN_INCLUSIVE:
            return value <= condition_version_info
        elif self.operator == NOT_EQUAL:
            return value != condition_version_info

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
