import logging
import typing
import uuid
from copy import deepcopy

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_CREATE,
    BEFORE_CREATE,
    LifecycleModelMixin,
    hook,
)
from flag_engine.segments import constants

from audit.constants import (
    SEGMENT_CREATED_MESSAGE,
    SEGMENT_DELETED_MESSAGE,
    SEGMENT_UPDATED_MESSAGE,
)
from audit.related_object_type import RelatedObjectType
from core.models import (
    SoftDeleteExportableManager,
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory,
)
from features.models import Feature
from metadata.models import Metadata
from projects.models import Project

from .managers import LiveSegmentManager, SegmentManager

logger = logging.getLogger(__name__)


class Segment(
    LifecycleModelMixin,  # type: ignore[misc]
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),  # type: ignore[misc]
):
    history_record_class_path = "segments.models.HistoricalSegment"
    related_object_type = RelatedObjectType.SEGMENT

    name = models.CharField(max_length=2000)
    description = models.TextField(null=True, blank=True)
    project = models.ForeignKey(
        Project,
        # Cascade deletes are decouple from the Django ORM. See this PR for details.
        # https://github.com/Flagsmith/flagsmith/pull/3360/
        on_delete=models.DO_NOTHING,
        related_name="segments",
    )
    feature = models.ForeignKey(
        Feature, on_delete=models.CASCADE, related_name="segments", null=True
    )

    # This defaults to 1 for newly created segments.
    version = models.IntegerField(null=True)

    version_of = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="versioned_segments",
        null=True,
        blank=True,
    )

    change_request = models.ForeignKey(
        "workflows_core.ChangeRequest",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="segments",
    )

    metadata = GenericRelation(Metadata)

    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)

    objects = SegmentManager()  # type: ignore[misc]

    # Only serves segments that are the canonical version.
    live_objects = LiveSegmentManager()

    class Meta:
        ordering = ("id",)  # explicit ordering to prevent pagination warnings

    def __str__(self):  # type: ignore[no-untyped-def]
        return "Segment - %s" % self.name

    def get_skip_create_audit_log(self) -> bool:
        try:
            if self.version_of_id and self.version_of_id != self.id:
                return True
        except Segment.DoesNotExist:
            return True

        return False

    @hook(BEFORE_CREATE, when="version_of", is_now=None)
    def set_default_version_to_one_if_new_segment(self):  # type: ignore[no-untyped-def]
        if self.version is None:
            self.version = 1

    @hook(AFTER_CREATE, when="version_of", is_now=None)
    def set_version_of_to_self_if_none(self):  # type: ignore[no-untyped-def]
        """
        This allows the segment model to reference all versions of
        itself including itself.
        """
        self.version_of = self
        self.save_without_historical_record()

    @transaction.atomic
    def clone(self, is_revision: bool = False, **extra_attrs: typing.Any) -> "Segment":
        """
        Create a revision of the segment
        """
        cloned_segment = deepcopy(self)
        cloned_segment.pk = None
        cloned_segment.uuid = uuid.uuid4()
        cloned_segment.version_of = None  # Unset for now
        cloned_segment.version = 0  # Unset for now
        for attr_name, value in extra_attrs.items():
            setattr(cloned_segment, attr_name, value)
        cloned_segment.save()

        cloned_segment.copy_rules_and_conditions_from(self)

        # Handle versioning
        version_of = self if is_revision else cloned_segment
        cloned_segment.version_of = extra_attrs.get("version_of", version_of)
        cloned_segment.version = self.version if is_revision else 1
        Segment.objects.filter(pk=cloned_segment.pk).update(
            version_of=cloned_segment.version_of,
            version=cloned_segment.version,
        )

        # Increase self version
        if is_revision:
            self.version = (self.version or 1) + 1
            Segment.objects.filter(pk=self.pk).update(version=self.version)

        return cloned_segment

    def copy_rules_and_conditions_from(self, source_segment: "Segment") -> None:
        """
        Recursively copy rules and conditions from another segment
        """
        assert transaction.get_connection().in_atomic_block, "Must run in a transaction"

        # Delete existing rules
        SegmentRule.objects.filter(segment=self).delete()

        source_rules = SegmentRule.objects.filter(
            models.Q(segment=source_segment) | models.Q(rule__segment=source_segment)
        )

        # Ensure top-level rules are cloned first (for dependencies)
        source_rules = source_rules.order_by(models.F("rule").asc(nulls_first=True))

        rule_to_cloned_rule_map: dict[SegmentRule, SegmentRule] = {}
        for rule in source_rules:
            cloned_rule = deepcopy(rule)
            cloned_rule.pk = None
            cloned_rule.uuid = uuid.uuid4()
            cloned_rule.segment = self if rule.segment else None
            cloned_rule.rule = rule_to_cloned_rule_map.get(rule.rule)
            cloned_rule.save()
            rule_to_cloned_rule_map[rule] = cloned_rule

        source_conditions = Condition.objects.filter(rule__in=rule_to_cloned_rule_map)
        for condition in source_conditions:
            cloned_condition = deepcopy(condition)
            cloned_condition.pk = None
            cloned_condition.uuid = uuid.uuid4()
            cloned_condition.rule = rule_to_cloned_rule_map[condition.rule]
            cloned_condition.save()

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:  # type: ignore[no-untyped-def]
        return SEGMENT_CREATED_MESSAGE % self.name

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:  # type: ignore[no-untyped-def]
        return SEGMENT_UPDATED_MESSAGE % self.name

    def get_delete_log_message(self, history_instance) -> typing.Optional[str]:  # type: ignore[no-untyped-def]
        return SEGMENT_DELETED_MESSAGE % self.name

    def _get_project(self):  # type: ignore[no-untyped-def]
        return self.project


class SegmentRule(
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),  # type: ignore[misc]
):
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

    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)

    history_record_class_path = "segments.models.HistoricalSegmentRule"

    def clean(self):  # type: ignore[no-untyped-def]
        super().clean()
        parents = [self.segment, self.rule]
        num_parents = sum(parent is not None for parent in parents)
        if num_parents != 1:
            raise ValidationError(
                "Segment rule must have exactly one parent, %d found",
                num_parents,  # type: ignore[arg-type]
            )

    def __str__(self):  # type: ignore[no-untyped-def]
        return "%s rule for %s" % (
            self.type,
            str(self.segment) if self.segment else str(self.rule),
        )

    def get_skip_create_audit_log(self) -> bool:
        try:
            segment = self.get_segment()  # type: ignore[no-untyped-call]
            if segment.deleted_at:
                return True
            return segment.version_of_id != segment.id  # type: ignore[no-any-return]
        except (Segment.DoesNotExist, SegmentRule.DoesNotExist):
            # handle hard delete
            return True

    def _get_project(self) -> typing.Optional[Project]:
        return self.get_segment().project  # type: ignore[no-untyped-call,no-any-return]

    def get_segment(self):  # type: ignore[no-untyped-def]
        """
        rules can be a child of a parent rule instead of a segment, this method iterates back up the tree to find the
        segment

        TODO: denormalise the segment information so that we don't have to make multiple queries here in complex cases
        """
        rule = self
        while not rule.segment_id:
            rule = rule.rule  # type: ignore[assignment]
        return rule.segment


class ConditionManager(SoftDeleteExportableManager):
    def get_queryset(
        self,
    ) -> models.QuerySet["Condition"]:
        # Effectively `Condition.Meta.ordering = ("id",) if ... else ()`,
        # but avoid the weirdness of a setting-dependant migration
        # and having to reload everything in tests
        qs: models.QuerySet["Condition"]
        if settings.SEGMENT_RULES_CONDITIONS_EXPLICIT_ORDERING_ENABLED:
            qs = super().get_queryset().order_by("id")
        else:
            qs = super().get_queryset()
        return qs


class Condition(
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),  # type: ignore[misc]
):
    history_record_class_path = "segments.models.HistoricalCondition"
    related_object_type = RelatedObjectType.SEGMENT

    CONDITION_TYPES = (
        (constants.EQUAL, "Exactly Matches"),
        (constants.GREATER_THAN, "Greater than"),
        (constants.LESS_THAN, "Less than"),
        (constants.CONTAINS, "Contains"),
        (constants.GREATER_THAN_INCLUSIVE, "Greater than or equal to"),
        (constants.LESS_THAN_INCLUSIVE, "Less than or equal to"),
        (constants.NOT_CONTAINS, "Does not contain"),
        (constants.NOT_EQUAL, "Does not match"),
        (constants.REGEX, "Matches regex"),
        (constants.PERCENTAGE_SPLIT, "Percentage split"),
        (constants.MODULO, "Modulo Operation"),
        (constants.IS_SET, "Is set"),
        (constants.IS_NOT_SET, "Is not set"),
        (constants.IN, "In"),
    )

    operator = models.CharField(choices=CONDITION_TYPES, max_length=500)
    property = models.CharField(null=True, max_length=1000)
    value = models.CharField(
        max_length=settings.SEGMENT_CONDITION_VALUE_LIMIT, blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)

    created_with_segment = models.BooleanField(
        default=False,
        help_text="Field to denote whether a condition was created along with segment or added after creation.",
    )

    rule = models.ForeignKey(
        SegmentRule, on_delete=models.CASCADE, related_name="conditions"
    )

    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)

    objects: typing.ClassVar[ConditionManager] = ConditionManager()

    def __str__(self):  # type: ignore[no-untyped-def]
        return "Condition for %s: %s %s %s" % (
            str(self.rule),
            self.property,
            self.operator,
            self.value,
        )

    def get_skip_create_audit_log(self) -> bool:
        try:
            if self.rule.deleted_at:
                return True

            segment = self.rule.get_segment()  # type: ignore[no-untyped-call]
            if segment.deleted_at:
                return True

            return segment.version_of_id != segment.id  # type: ignore[no-any-return]
        except (Segment.DoesNotExist, SegmentRule.DoesNotExist):
            # handle hard delete
            return True

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:  # type: ignore[no-untyped-def]
        return f"Condition updated on segment '{self._get_segment().name}'."

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:  # type: ignore[no-untyped-def,return]
        if not self.created_with_segment:
            return f"Condition added to segment '{self._get_segment().name}'."

    def get_delete_log_message(self, history_instance) -> typing.Optional[str]:  # type: ignore[no-untyped-def,return]
        if not self._get_segment().deleted_at:
            return f"Condition removed from segment '{self._get_segment().name}'."

    def get_audit_log_related_object_id(self, history_instance) -> int:  # type: ignore[no-untyped-def]
        return self._get_segment().id

    def _get_segment(self) -> Segment:
        """
        Temporarily cache the segment on the condition object to reduce number of queries.
        """
        if not hasattr(self, "segment"):
            setattr(self, "segment", self.rule.get_segment())  # type: ignore[no-untyped-call]
        return self.segment  # type: ignore[no-any-return]

    def _get_project(self) -> typing.Optional[Project]:
        return self.rule.get_segment().project  # type: ignore[no-untyped-call,no-any-return]


class WhitelistedSegment(models.Model):
    """
    In order to grandfather in existing segments, these models represent segments
    that do not conform to the SEGMENT_RULES_CONDITIONS_LIMIT and may have
    more than the typically allowed number of segment rules and conditions.
    """

    segment = models.OneToOneField(
        Segment,
        on_delete=models.CASCADE,
        related_name="whitelisted_segment",
    )
    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)
