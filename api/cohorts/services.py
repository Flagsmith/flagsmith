import csv
import io
import typing

import structlog
from django.db import transaction
from django.db.models import F, QuerySet
from django.utils import timezone
from flag_engine.segments.constants import IS_SET
from rest_framework.exceptions import ValidationError

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
from cohorts.models import Cohort, CohortMembership, CohortMembershipState
from core.dataclasses import AuthorData
from environments.dynamodb import DynamoIdentityWrapper
from segments.models import Condition, Segment, SegmentManagedBy, SegmentRule
from segments.services import delete_segment

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from projects.models import Project

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


def edge_sync_enabled(project: "Project") -> bool:
    return bool(project.enable_dynamo_db and DynamoIdentityWrapper().is_enabled)


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
