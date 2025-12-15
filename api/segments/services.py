import typing
import uuid

from django.db import models, transaction
from django.utils import timezone

from core.dataclasses import AuthorData

if typing.TYPE_CHECKING:
    from segments.models import Segment


def delete_segment(
    segment: "Segment",
    author: AuthorData,
) -> None:
    """
    Delete a segment using optimized bulk operations.

    Uses bulk UPDATE/DELETE operations instead of individual soft-deletes,
    reducing the number of database queries from O(n) to O(1) where n is
    the number of rules and conditions.

    Note: This is a temporary solution until we redesign the segment data model.
    """
    from features.models import FeatureSegment
    from segments.models import Condition, Segment, SegmentRule
    from segments.tasks import create_segment_deleted_audit_log

    now = timezone.now()

    segment_name = segment.name
    segment_uuid = str(segment.uuid)
    segment_id = segment.id
    project_id = segment.project_id

    segment_ids = list(
        Segment.objects.filter(
            models.Q(id=segment.id) | models.Q(version_of_id=segment.id)
        ).values_list("id", flat=True)
    )

    top_level_rule_ids = list(
        SegmentRule.objects.filter(segment_id__in=segment_ids).values_list(
            "id", flat=True
        )
    )

    all_rule_ids = set(top_level_rule_ids)
    current_level_ids = top_level_rule_ids

    while current_level_ids:
        nested_rule_ids = list(
            SegmentRule.objects.filter(rule_id__in=current_level_ids).values_list(
                "id", flat=True
            )
        )
        all_rule_ids.update(nested_rule_ids)
        current_level_ids = nested_rule_ids

    all_rule_ids_list = list(all_rule_ids)

    with transaction.atomic():
        FeatureSegment.objects.filter(segment_id__in=segment_ids).delete()
        Condition.objects.filter(rule_id__in=all_rule_ids_list).update(deleted_at=now)
        SegmentRule.objects.filter(id__in=all_rule_ids_list).update(deleted_at=now)
        Segment.objects.filter(id__in=segment_ids).update(deleted_at=now)

    create_segment_deleted_audit_log.delay(
        args=(
            project_id,
            segment_name,
            segment_id,
            segment_uuid,
            author.user.id if author.user else None,
            author.api_key.id if author.api_key else None,
            now.isoformat(),
        )
    )


def copy_segment_rules_and_conditions(
    target_segment: "Segment",
    source_segment: "Segment",
) -> None:
    """
    Copy rules and conditions from source to target segment using bulk operations.

    If target has existing rules, they are hard-deleted first.

    """
    from segments.models import Condition, SegmentRule

    assert transaction.get_connection().in_atomic_block, "Must run in a transaction"

    SegmentRule.objects.filter(segment=target_segment).delete()

    top_level_rules = list(SegmentRule.objects.filter(segment=source_segment))
    if not top_level_rules:
        return

    rule_id_to_cloned_rule: dict[int, SegmentRule] = {}

    cloned_top_rules = [
        SegmentRule(
            uuid=uuid.uuid4(),
            segment=target_segment,
            rule=None,
            type=rule.type,
        )
        for rule in top_level_rules
    ]
    SegmentRule.objects.bulk_create(cloned_top_rules)

    for rule, cloned in zip(top_level_rules, cloned_top_rules):
        rule_id_to_cloned_rule[rule.id] = cloned

    current_level_rule_ids = [r.id for r in top_level_rules]
    while current_level_rule_ids:
        nested_rules = list(
            SegmentRule.objects.filter(rule_id__in=current_level_rule_ids)
        )
        cloned_nested = []
        for rule in nested_rules:
            assert rule.rule_id is not None
            cloned_nested.append(
                SegmentRule(
                    uuid=uuid.uuid4(),
                    segment=None,
                    rule=rule_id_to_cloned_rule[rule.rule_id],
                    type=rule.type,
                )
            )

        if cloned_nested:
            SegmentRule.objects.bulk_create(cloned_nested)

        for rule, cloned in zip(nested_rules, cloned_nested):
            rule_id_to_cloned_rule[rule.id] = cloned

        current_level_rule_ids = [r.id for r in nested_rules]

    source_conditions = list(
        Condition.objects.filter(rule_id__in=rule_id_to_cloned_rule.keys())
    )
    if source_conditions:
        Condition.objects.bulk_create(
            [
                Condition(
                    uuid=uuid.uuid4(),
                    rule=rule_id_to_cloned_rule[c.rule_id],
                    operator=c.operator,
                    property=c.property,
                    value=c.value,
                    description=c.description,
                    created_with_segment=True,
                )
                for c in source_conditions
            ]
        )
