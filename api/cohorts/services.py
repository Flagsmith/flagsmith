import csv
import io
import typing
from uuid import UUID

import structlog
from django.db import transaction
from django.db.models import F, QuerySet
from django.utils import timezone
from flag_engine.segments.constants import IS_SET
from rest_framework.exceptions import ValidationError

from audit.constants import SEGMENT_CREATED_MESSAGE
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from cohorts.constants import (
    COHORT_CSV_MEMBERSHIP_WRITE_BATCH_SIZE,
    COHORT_IDENTIFIER_MAX_BYTES,
    COHORT_MEMBERSHIP_APPLY_BATCH_SIZE,
)
from cohorts.dataclasses import (
    CohortCsvIgnoredRows,
    CohortCsvSyncResult,
    CsvIdentifierExtraction,
)
from cohorts.metrics import (
    flagsmith_cohorts_csv_sync_identifiers,
    flagsmith_cohorts_csv_syncs_total,
    flagsmith_cohorts_membership_deltas_applied_total,
)
from cohorts.models import (
    Cohort,
    CohortMembership,
    CohortMembershipState,
    CohortSourceType,
)
from core.dataclasses import AuthorData
from edge_api.utils import is_edge_enabled
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

_T = typing.TypeVar("_T")


def _batched(
    items: list[_T], size: int = COHORT_CSV_MEMBERSHIP_WRITE_BATCH_SIZE
) -> typing.Iterator[list[_T]]:
    for offset in range(0, len(items), size):
        yield items[offset : offset + size]


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
    external_id: str | None = None,
) -> Cohort:
    project = environment.project
    # Mirrors the segment limit enforced by SegmentSerializer, which cohort
    # creation bypasses by creating its managed segment directly.
    if (
        is_edge_enabled()
        and Segment.live_objects.filter(project=project).count()
        >= project.max_segments_allowed
    ):
        raise ValidationError(
            {"project": ["The project has reached the maximum allowed segments limit."]}
        )
    with transaction.atomic():
        segment = Segment.objects.create(
            name=name,
            project=environment.project,
            description=description,
            managed_by=SegmentManagedBy.COHORT,
        )
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        cohort: Cohort = Cohort.objects.create(
            environment=environment,
            segment=segment,
            source_type=source_type,
            external_id=external_id,
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
    external_id: str | None = None,
) -> Cohort:
    """Create a cohort on behalf of an external source, where no Flagsmith
    user is acting."""
    cohort = create_cohort(
        environment=environment,
        name=name,
        source_type=source_type,
        external_id=external_id,
    )
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


def get_active_cohort(
    *,
    environment: "Environment",
    source_type: CohortSourceType,
    uuid: str,
) -> Cohort | None:
    try:
        cohort_uuid = UUID(uuid)
    except ValueError:
        return None
    cohort: Cohort | None = Cohort.objects.filter(
        uuid=cohort_uuid,
        environment=environment,
        source_type=source_type,
        deletion_requested_at__isnull=True,
    ).first()
    return cohort


def get_cohort_for_source(
    *,
    environment: "Environment",
    source_type: CohortSourceType,
    external_id: str,
) -> Cohort | None:
    cohort: Cohort | None = Cohort.objects.filter(
        environment=environment,
        source_type=source_type,
        external_id=external_id,
        deletion_requested_at__isnull=True,
    ).first()
    return cohort


def cohort_deletion_in_progress(
    *,
    environment: "Environment",
    source_type: CohortSourceType,
    external_id: str,
) -> bool:
    return bool(
        Cohort.objects.filter(
            environment=environment,
            source_type=source_type,
            external_id=external_id,
            deletion_requested_at__isnull=False,
        ).exists()
    )


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
        "membership.adds_received",
        cohort__id=cohort.id,
        environment__id=cohort.environment_id,
        deltas__count=len(rows),
    )


def remove_cohort_members(cohort: Cohort, identifiers: "typing.Iterable[str]") -> None:
    from cohorts.tasks import apply_cohort_membership_deltas

    unique_identifiers = list(set(identifiers))
    matched = 0
    with transaction.atomic():
        # Postgres rejects a statement carrying more than 65535 bind
        # parameters, which a single large identifier list would exceed.
        for start in range(0, len(unique_identifiers), 1000):
            # Removing a non-member is a no-op: only existing rows flip.
            matched += CohortMembership.objects.filter(
                cohort=cohort,
                identifier__in=unique_identifiers[start : start + 1000],
            ).update(
                state=CohortMembershipState.PENDING_REMOVE, updated_at=timezone.now()
            )
        apply_cohort_membership_deltas.delay(kwargs={"cohort_id": cohort.id})
    logger.info(
        "membership.removals_received",
        cohort__id=cohort.id,
        environment__id=cohort.environment_id,
        deltas__count=len(unique_identifiers),
        members__matched=matched,
    )


def extract_identifiers_from_csv(
    file: typing.IO[bytes],
    *,
    identifier_column: int = 0,
    has_header: bool = True,
) -> CsvIdentifierExtraction:
    # The upload size cap keeps a full read cheap.
    text = io.StringIO(file.read().decode("utf-8-sig", errors="replace"), newline="")
    reader = csv.reader(text)
    seen: set[str] = set()
    identifiers: list[str] = []
    empty_count = duplicate_count = too_long_count = 0
    try:
        for row_number, row in enumerate(reader):
            if has_header and row_number == 0:
                continue
            if not row:
                continue
            value = (
                row[identifier_column].strip() if identifier_column < len(row) else ""
            )
            if not value:
                empty_count += 1
            elif len(value.encode()) > COHORT_IDENTIFIER_MAX_BYTES:
                too_long_count += 1
            elif value in seen:
                duplicate_count += 1
            else:
                seen.add(value)
                identifiers.append(value)
    except csv.Error as exc:
        raise ValidationError({"file": "Could not parse the CSV file."}) from exc
    return CsvIdentifierExtraction(
        identifiers=identifiers,
        empty_count=empty_count,
        duplicate_count=duplicate_count,
        too_long_count=too_long_count,
    )


def sync_cohort_memberships_from_csv(
    *,
    cohort: Cohort,
    file: typing.IO[bytes],
    identifier_column: int = 0,
    has_header: bool = True,
) -> CohortCsvSyncResult:
    from cohorts.tasks import apply_cohort_membership_deltas

    extraction = extract_identifiers_from_csv(
        file, identifier_column=identifier_column, has_header=has_header
    )
    if not extraction.identifiers:
        raise ValidationError({"file": "No valid identifiers found in the CSV file."})

    # A sync is a full reconciliation towards the uploaded CSV: a partially
    # failed or interleaved run converges on the next upload, and the unique
    # constraint absorbs concurrent inserts. Writes are therefore chunked into
    # their own implicit transactions instead of one long transaction that
    # would hold locks against the applier task while a 10 MB file lands.
    incoming = set(extraction.identifiers)
    existing = {
        membership.identifier: membership
        for membership in CohortMembership.objects.filter(cohort=cohort).only(
            "id", "identifier", "state"
        )
    }
    to_create = [
        identifier
        for identifier in extraction.identifiers
        if identifier not in existing
    ]
    present = incoming & existing.keys()
    readd_ids = [
        existing[identifier].id
        for identifier in present
        if existing[identifier].state == CohortMembershipState.PENDING_REMOVE
    ]
    # A departed pending add may have had its trait written by a concurrent
    # applier run, so drain it via pending remove, never delete.
    remove_ids = [
        membership.id
        for identifier, membership in existing.items()
        if identifier not in incoming
        and membership.state != CohortMembershipState.PENDING_REMOVE
    ]

    for identifier_batch in _batched(to_create):
        CohortMembership.objects.bulk_create(
            [
                CohortMembership(cohort=cohort, identifier=identifier)
                for identifier in identifier_batch
            ],
            ignore_conflicts=True,
        )
    added = len(to_create)
    removed = 0
    unchanged = len(present) - len(readd_ids)
    for id_batch in _batched(readd_ids):
        added += CohortMembership.objects.filter(id__in=id_batch).update(
            state=CohortMembershipState.PENDING_ADD, updated_at=timezone.now()
        )
    for id_batch in _batched(remove_ids):
        removed += CohortMembership.objects.filter(id__in=id_batch).update(
            state=CohortMembershipState.PENDING_REMOVE, updated_at=timezone.now()
        )

    Cohort.objects.filter(id=cohort.id).update(version=F("version") + 1)
    cohort.refresh_from_db(fields=["version"])
    apply_cohort_membership_deltas.delay(kwargs={"cohort_id": cohort.id})

    flagsmith_cohorts_csv_syncs_total.inc()
    flagsmith_cohorts_csv_sync_identifiers.observe(len(incoming))
    logger.info(
        "csv.synced",
        cohort__id=cohort.id,
        environment__id=cohort.environment_id,
        cohort__version=cohort.version,
        adds__count=added,
        removes__count=removed,
        unchanged__count=unchanged,
    )
    return CohortCsvSyncResult(
        version=cohort.version,
        added=added,
        removed=removed,
        unchanged=unchanged,
        ignored=CohortCsvIgnoredRows(
            empty=extraction.empty_count,
            duplicates=extraction.duplicate_count,
            too_long=extraction.too_long_count,
        ),
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
