import logging
import typing
from copy import deepcopy

import semver
from core.constants import BOOLEAN, FLOAT, INTEGER
from core.models import (
    AbstractBaseExportableModel,
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory,
)
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from flag_engine.utils.semver import is_semver, remove_semver_suffix

from audit.constants import SEGMENT_CREATED_MESSAGE, SEGMENT_UPDATED_MESSAGE
from audit.related_object_type import RelatedObjectType
from environments.identities.helpers import (
    get_hashed_percentage_for_object_ids,
)
from features.models import Feature
from metadata.models import Metadata
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
MODULO = "MODULO"
IS_SET = "IS_SET"
IS_NOT_SET = "IS_NOT_SET"
IN = "IN"


class Segment(
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),
):
    history_record_class_path = "segments.models.HistoricalSegment"
    related_object_type = RelatedObjectType.SEGMENT

    name = models.CharField(max_length=2000)
    description = models.TextField(null=True, blank=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="segments"
    )
    feature = models.ForeignKey(
        Feature, on_delete=models.CASCADE, related_name="segments", null=True
    )

    metadata = GenericRelation(Metadata)

    class Meta:
        ordering = ("id",)  # explicit ordering to prevent pagination warnings

    def __str__(self):
        return "Segment - %s" % self.name

    @staticmethod
    def id_exists_in_rules_data(rules_data: typing.List[dict]) -> bool:
        """
        Given a list of segment rules, return whether any of the rules or conditions contain an id.

        :param rules_data: list of segment rules (in the form {"id": 1, "rules": [], "conditions": [], "typing": ""})
        :return: boolean value detailing whether any id attributes were found
        """

        _rules_data = deepcopy(rules_data)
        for rule_data in _rules_data:
            if rule_data.get("id"):
                return True

            conditions_to_check = rule_data.get("conditions", [])
            rules_to_check = rule_data.get("rules", [])

            while rules_to_check:
                rule = rules_to_check.pop()
                if rule.get("id"):
                    return True
                rules_to_check.extend(rule.get("rules", []))
                conditions_to_check.extend(rule.get("conditions", []))

            while conditions_to_check:
                condition = conditions_to_check.pop()
                if condition.get("id"):
                    return True

        return False

    def does_identity_match(
        self, identity: "Identity", traits: typing.List["Trait"] = None
    ) -> bool:
        rules = self.rules.all()
        return rules.count() > 0 and all(
            rule.does_identity_match(identity, traits) for rule in rules
        )

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:
        return SEGMENT_CREATED_MESSAGE % self.name

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        return SEGMENT_UPDATED_MESSAGE % self.name

    def _get_project(self):
        return self.project


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


class Condition(
    AbstractBaseExportableModel, abstract_base_auditable_model_factory(["uuid"])
):
    history_record_class_path = "segments.models.HistoricalCondition"
    related_object_type = RelatedObjectType.SEGMENT

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
        (MODULO, "Modulo Operation"),
        (IS_SET, "Is set"),
        (IS_NOT_SET, "Is not set"),
        (IN, "In"),
    )

    operator = models.CharField(choices=CONDITION_TYPES, max_length=500)
    property = models.CharField(blank=True, null=True, max_length=1000)
    value = models.CharField(max_length=1000, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    created_with_segment = models.BooleanField(
        default=False,
        help_text="Field to denote whether a condition was created along with segment or added after creation.",
    )

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

    def does_identity_match(  # noqa: C901
        self, identity: "Identity", traits: typing.List["Trait"] = None
    ) -> bool:
        if self.operator == PERCENTAGE_SPLIT:
            return self._check_percentage_split_operator(identity)

        # we allow passing in traits to handle when they aren't
        # persisted for certain organisations
        traits = identity.identity_traits.all() if traits is None else traits
        matching_trait = next(
            filter(lambda t: t.trait_key == self.property, traits), None
        )
        if matching_trait is None:
            return self.operator == IS_NOT_SET

        if self.operator in (IS_SET, IS_NOT_SET):
            return self.operator == IS_SET
        elif self.operator == MODULO:
            if matching_trait.value_type in [INTEGER, FLOAT]:
                return self._check_modulo_operator(matching_trait.trait_value)
        elif self.operator == IN:
            return str(matching_trait.trait_value) in self.value.split(",")
        elif matching_trait.value_type == INTEGER:
            return self.check_integer_value(matching_trait.integer_value)
        elif matching_trait.value_type == FLOAT:
            return self.check_float_value(matching_trait.float_value)
        elif matching_trait.value_type == BOOLEAN:
            return self.check_boolean_value(matching_trait.boolean_value)
        elif is_semver(self.value):
            return self.check_semver_value(matching_trait.string_value)

        return self.check_string_value(matching_trait.string_value)

    def _check_percentage_split_operator(self, identity):
        try:
            float_value = float(self.value) / 100.0
        except ValueError:
            return False

        segment = self.rule.get_segment()
        return (
            get_hashed_percentage_for_object_ids(
                object_ids=[segment.id, identity.get_hash_key()]
            )
            <= float_value
        )

    def _check_modulo_operator(self, value: typing.Union[int, float]) -> bool:
        try:
            divisor, remainder = self.value.split("|")
            divisor = float(divisor)
            remainder = float(remainder)
        except ValueError:
            return False

        return value % divisor == remainder

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

        return False

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        return f"Condition updated on segment '{self._get_segment().name}'."

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:
        if not self.created_with_segment:
            return f"Condition added to segment '{self._get_segment().name}'."

    def get_delete_log_message(self, history_instance) -> typing.Optional[str]:
        if not self._get_segment().deleted_at:
            return f"Condition removed from segment '{self._get_segment().name}'."

    def get_audit_log_related_object_id(self, history_instance) -> int:
        return self._get_segment().id

    def _get_segment(self) -> Segment:
        """
        Temporarily cache the segment on the condition object to reduce number of queries.
        """
        if not hasattr(self, "segment"):
            setattr(self, "segment", self.rule.get_segment())
        return self.segment

    def _get_project(self) -> typing.Optional[Project]:
        return self.rule.get_segment().project
