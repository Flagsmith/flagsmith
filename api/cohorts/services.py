import structlog
from django.db.models import F, Func, IntegerField, QuerySet
from django.utils import timezone

from cohorts.constants import COHORT_MEMBERSHIP_APPLY_BATCH_SIZE
from cohorts.metrics import flagsmith_cohorts_membership_deltas_applied_total
from cohorts.models import Cohort, CohortMembership, CohortMembershipState
from environments.dynamodb import DynamoIdentityWrapper
from environments.dynamodb.constants import IDENTITY_SORT_KEY_MAX_BYTES

logger = structlog.get_logger("cohorts")

_PENDING_STATES = [
    CohortMembershipState.PENDING_ADD,
    CohortMembershipState.PENDING_REMOVE,
]


def _pending(cohort: Cohort) -> "QuerySet[CohortMembership]":
    return CohortMembership.objects.filter(
        cohort=cohort, state__in=_PENDING_STATES
    ).annotate(
        identifier_bytes=Func(
            F("identifier"), function="octet_length", output_field=IntegerField()
        )
    )


def pending_memberships(cohort: Cohort) -> "QuerySet[CohortMembership]":
    """Ledger rows awaiting application to the edge store.

    Identifiers over the DynamoDB sort-key byte cap are excluded — they can
    never exist as edge identities, and one would otherwise head every
    batch and stall the drain.
    """
    return _pending(cohort).filter(  # type: ignore[misc] # annotate() alias opaque to django-stubs
        identifier_bytes__lte=IDENTITY_SORT_KEY_MAX_BYTES
    )


def apply_pending_memberships(cohort: Cohort) -> bool:
    """Apply one batch of pending ledger rows to DynamoDB identity documents.

    Returns True while pending rows remain — callers loop until False.
    Raises `SystemTraitWriteRaceError` on unwinnable write contention and
    propagates `ClientError` (callers map throttle codes to backoff).

    Lock-free: writes only touch the `system_traits.<cohort key>` attribute,
    and state flips are guarded — rows transitioned elsewhere mid-flight are
    left for a later batch. A crash re-applies the batch (idempotent).
    The ledger doubles as the durable membership table: applied adds are
    kept as `applied` rows (they serve core evaluation lookups); applied
    removes delete the row.
    """
    identity_wrapper = DynamoIdentityWrapper()
    environment_api_key: str = cohort.environment.api_key
    trait_key = cohort.system_trait_key
    batch = list(
        pending_memberships(cohort).order_by("id")[:COHORT_MEMBERSHIP_APPLY_BATCH_SIZE]
    )
    if not batch:
        _warn_if_unappliable(cohort)
        return False
    added_ids: list[int] = []
    removed_ids: list[int] = []
    for row in batch:
        # Re-read just before writing: narrows the stale-claim window from
        # the batch's whole duration to a single write's. The residual race
        # is repaired by the reconciliation sweep (see design doc).
        state = (
            CohortMembership.objects.filter(id=row.id)
            .values_list("state", flat=True)
            .first()
        )
        if state == CohortMembershipState.PENDING_ADD:
            identity_wrapper.set_system_trait(
                environment_api_key=environment_api_key,
                identifier=row.identifier,
                trait_key=trait_key,
            )
            added_ids.append(row.id)
        elif state == CohortMembershipState.PENDING_REMOVE:
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
    remaining = pending_memberships(cohort).exists()
    if not remaining:
        _warn_if_unappliable(cohort)
    return remaining


def _warn_if_unappliable(cohort: Cohort) -> None:
    oversized_count = (
        _pending(cohort)
        .filter(  # type: ignore[misc] # annotate() alias opaque to django-stubs
            identifier_bytes__gt=IDENTITY_SORT_KEY_MAX_BYTES
        )
        .count()
    )
    if oversized_count:
        logger.warning(
            "membership.apply.oversized_identifiers",
            cohort__id=cohort.id,
            environment__id=cohort.environment_id,
            memberships__count=oversized_count,
        )
