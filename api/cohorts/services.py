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
from environments.dynamodb import DynamoIdentityWrapper
from segments.models import Condition, Segment, SegmentRule
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
    identity_wrapper = DynamoIdentityWrapper()
    environment_api_key: str = cohort.environment.api_key
    trait_key = cohort.system_trait_key
    batch = list(
        pending_memberships(cohort).order_by("id")[:COHORT_MEMBERSHIP_APPLY_BATCH_SIZE]
    )
    if not batch:
        return False
    added_ids: list[int] = []
    removed_ids: list[int] = []
    for row in batch:
        if row.state == CohortMembershipState.PENDING_ADD:
            identity_wrapper.set_system_trait(
                environment_api_key=environment_api_key,
                identifier=row.identifier,
                trait_key=trait_key,
            )
            added_ids.append(row.id)
        else:
            identity_wrapper.unset_system_trait(
                environment_api_key=environment_api_key,
                identifier=row.identifier,
                trait_key=trait_key,
            )
            removed_ids.append(row.id)
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


def create_cohort(*, environment: "Environment", name: str) -> Cohort:
    with transaction.atomic():
        segment = Segment.objects.create(name=name, project=environment.project)
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

    cohort.deletion_requested_at = timezone.now()
    cohort.save(update_fields=["deletion_requested_at"])
    if not (
        cohort.environment.project.enable_dynamo_db
        and DynamoIdentityWrapper().is_enabled
    ):
        finalise_cohort_deletion(cohort)
        return
    CohortMembership.objects.filter(cohort=cohort).update(
        state=CohortMembershipState.PENDING_REMOVE, updated_at=timezone.now()
    )
    apply_cohort_membership_deltas.delay(kwargs={"cohort_id": cohort.id})
    logger.info(
        "cohort.deletion_requested",
        cohort__id=cohort.id,
        environment__id=cohort.environment_id,
    )


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
