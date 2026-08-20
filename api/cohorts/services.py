import typing

import structlog
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from flag_engine.segments.constants import IS_SET

from audit.constants import SEGMENT_CREATED_MESSAGE
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from cohorts.constants import COHORT_MEMBERSHIP_APPLY_BATCH_SIZE
from cohorts.metrics import flagsmith_cohorts_membership_deltas_applied_total
from cohorts.models import (
    Cohort,
    CohortMembership,
    CohortMembershipState,
    CohortSourceType,
)
from core.dataclasses import AuthorData
from environments.identities.system_traits import (
    set_system_trait,
    unset_system_trait,
)
from segments.models import Condition, Segment, SegmentManagedBy, SegmentRule
from segments.services import delete_segment

if typing.TYPE_CHECKING:
    from environments.models import Environment

logger = structlog.get_logger("cohorts")

_PENDING_STATES = [
    CohortMembershipState.PENDING_ADD,
    CohortMembershipState.PENDING_REMOVE,
]


def pending_memberships(cohort: Cohort) -> "QuerySet[CohortMembership]":
    return CohortMembership.objects.filter(cohort=cohort, state__in=_PENDING_STATES)


def apply_pending_memberships(cohort: Cohort) -> bool:
    batch = list(
        pending_memberships(cohort).order_by("id")[:COHORT_MEMBERSHIP_APPLY_BATCH_SIZE]
    )
    if not batch:
        return False
    added_ids: list[int] = []
    removed_ids: list[int] = []
    added_identifiers: list[str] = []
    removed_identifiers: list[str] = []
    for row in batch:
        if row.state == CohortMembershipState.PENDING_ADD:
            added_ids.append(row.id)
            added_identifiers.append(row.identifier)
        else:
            removed_ids.append(row.id)
            removed_identifiers.append(row.identifier)
    environment = cohort.environment
    trait_key = cohort.system_trait_key
    set_system_trait(environment, trait_key, added_identifiers)
    unset_system_trait(environment, trait_key, removed_identifiers)
    added_count = CohortMembership.objects.filter(
        id__in=added_ids, state=CohortMembershipState.PENDING_ADD
    ).update(state=CohortMembershipState.APPLIED, updated_at=timezone.now())
    removed_count, _ = CohortMembership.objects.filter(
        id__in=removed_ids, state=CohortMembershipState.PENDING_REMOVE
    ).delete()
    flagsmith_cohorts_membership_deltas_applied_total.labels(operation="add").inc(
        added_count
    )
    flagsmith_cohorts_membership_deltas_applied_total.labels(operation="remove").inc(
        removed_count
    )
    if added_count or removed_count:
        logger.info(
            "membership.applied",
            cohort__id=cohort.id,
            environment__id=cohort.environment_id,
            adds__count=added_count,
            removes__count=removed_count,
        )
    return pending_memberships(cohort).exists()


def create_cohort(
    *,
    environment: "Environment",
    name: str,
    description: str | None = None,
    source_type: CohortSourceType = CohortSourceType.CSV,
) -> Cohort:
    with transaction.atomic():
        segment = Segment.objects.create(
            name=name,
            project=environment.project,
            description=description,
            managed_by=SegmentManagedBy.COHORT,
        )
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        cohort: Cohort = Cohort.objects.create(
            environment=environment, segment=segment, source_type=source_type
        )
        Condition.objects.create(
            rule=rule,
            operator=IS_SET,
            property=cohort.system_trait_key,
            created_with_segment=True,
        )
    logger.info(
        "cohort.created",
        cohort__id=cohort.id,
        segment__id=segment.id,
        environment__id=environment.id,
        project__id=environment.project_id,
        organisation__id=environment.project.organisation_id,
    )
    return cohort


def create_cohort_for_source(
    *,
    environment: "Environment",
    name: str,
    source_type: CohortSourceType,
) -> Cohort:
    """Create a cohort on behalf of an external source, where no Flagsmith
    user is acting."""
    cohort = create_cohort(environment=environment, name=name, source_type=source_type)
    # Nothing records a user for these calls, so the audit log that Flagsmith
    # derives from historical records is skipped — and with it the environment
    # document rebuild that makes the new segment visible to SDKs. Write the
    # record here instead, naming the source that asked for the cohort.
    AuditLog.objects.create(
        environment=environment,
        project=environment.project,
        related_object_id=cohort.segment_id,
        related_object_type=RelatedObjectType.SEGMENT.name,
        log=(
            f"{SEGMENT_CREATED_MESSAGE % cohort.segment.name} "
            f"(via {CohortSourceType(source_type).label} cohort sync)"
        ),
    )
    return cohort


def add_cohort_members(cohort: Cohort, identifiers: "typing.Iterable[str]") -> None:
    from cohorts.tasks import apply_cohort_membership_deltas

    rows = [
        CohortMembership(cohort=cohort, identifier=identifier)
        for identifier in set(identifiers)
    ]
    with transaction.atomic():
        # Re-adding a member is a no-op end to end: an applied row flips back
        # to pending and the identity write it triggers is idempotent.
        CohortMembership.objects.bulk_create(
            rows,
            # Postgres rejects a statement carrying more than 65535 bind
            # parameters, which a single large batch would exceed.
            batch_size=1000,
            update_conflicts=True,
            unique_fields=["cohort", "identifier"],
            update_fields=["state", "updated_at"],
        )
        apply_cohort_membership_deltas.delay(kwargs={"cohort_id": cohort.id})
    logger.info(
        "membership.deltas_received",
        cohort__id=cohort.id,
        environment__id=cohort.environment_id,
        action="add",
        deltas__count=len(rows),
    )


def remove_cohort_members(cohort: Cohort, identifiers: "typing.Iterable[str]") -> None:
    from cohorts.tasks import apply_cohort_membership_deltas

    unique_identifiers = set(identifiers)
    with transaction.atomic():
        # Removing a non-member is a no-op: only existing rows flip.
        matched = CohortMembership.objects.filter(
            cohort=cohort, identifier__in=unique_identifiers
        ).update(state=CohortMembershipState.PENDING_REMOVE, updated_at=timezone.now())
        apply_cohort_membership_deltas.delay(kwargs={"cohort_id": cohort.id})
    logger.info(
        "membership.deltas_received",
        cohort__id=cohort.id,
        environment__id=cohort.environment_id,
        action="remove",
        deltas__count=len(unique_identifiers),
        members__matched=matched,
    )


def delete_cohort(cohort: Cohort) -> None:
    from cohorts.tasks import apply_cohort_membership_deltas

    with transaction.atomic():
        cohort.deletion_requested_at = timezone.now()
        cohort.save(update_fields=["deletion_requested_at"])
        logger.info(
            "cohort.deletion_requested",
            cohort__id=cohort.id,
            environment__id=cohort.environment_id,
        )
        CohortMembership.objects.filter(cohort=cohort).update(
            state=CohortMembershipState.PENDING_REMOVE, updated_at=timezone.now()
        )
        apply_cohort_membership_deltas.delay(kwargs={"cohort_id": cohort.id})


def finalise_cohort_deletion(cohort: Cohort) -> None:
    segment = cohort.segment
    with transaction.atomic():
        cohort.delete()
        delete_segment(segment, AuthorData())
    logger.info(
        "cohort.deleted",
        cohort__id=cohort.id,
        environment__id=cohort.environment_id,
    )
