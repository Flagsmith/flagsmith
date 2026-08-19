import typing

import structlog
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from flag_engine.segments.constants import IS_SET

from cohorts.constants import COHORT_MEMBERSHIP_APPLY_BATCH_SIZE
from cohorts.metrics import flagsmith_cohorts_membership_deltas_applied_total
from cohorts.models import Cohort, CohortMembership, CohortMembershipState
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
) -> Cohort:
    with transaction.atomic():
        segment = Segment.objects.create(
            name=name,
            project=environment.project,
            description=description,
            managed_by=SegmentManagedBy.COHORT,
        )
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        cohort: Cohort = Cohort.objects.create(environment=environment, segment=segment)
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
