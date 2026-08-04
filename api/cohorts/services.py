import structlog
from botocore.exceptions import ClientError

from cohorts.constants import (
    COHORT_MEMBERSHIP_APPLY_BATCH_SIZE,
    COHORT_MEMBERSHIP_APPLY_MAX_ATTEMPTS,
)
from cohorts.exceptions import CohortMembershipApplyRaceError
from cohorts.metrics import flagsmith_cohorts_membership_deltas_applied_total
from cohorts.models import Cohort, CohortMembership, CohortMembershipState
from environments.dynamodb import DynamoIdentityWrapper
from util.engine_models.identities.models import IdentityModel
from util.mappers.dynamodb import map_engine_identity_to_identity_document

logger = structlog.get_logger("cohorts")

identity_wrapper = DynamoIdentityWrapper()


def apply_pending_memberships(cohort: Cohort) -> int:
    """Apply one batch of pending ledger rows to DynamoDB identity documents.

    Returns the number of rows processed; 0 means the ledger is drained.
    Lock-free: DynamoDB writes only touch the `system_traits.<cohort key>`
    attribute (conditional updates), so concurrent SDK writes are preserved,
    and state flips are guarded — rows transitioned elsewhere mid-flight are
    left for a later batch. A crash re-applies the batch (idempotent).
    """
    environment_api_key: str = cohort.environment.api_key
    trait_key = cohort.system_trait_key
    batch = list(
        CohortMembership.objects.filter(
            cohort=cohort,
            state__in=[
                CohortMembershipState.PENDING_ADD,
                CohortMembershipState.PENDING_REMOVE,
            ],
        ).order_by("id")[:COHORT_MEMBERSHIP_APPLY_BATCH_SIZE]
    )
    if not batch:
        return 0
    added_ids: list[int] = []
    removed_ids: list[int] = []
    for row in batch:
        composite_key = IdentityModel.generate_composite_key(
            environment_api_key, row.identifier
        )
        if row.state == CohortMembershipState.PENDING_ADD:
            _apply_add(composite_key, row.identifier, environment_api_key, trait_key)
            added_ids.append(row.id)
        else:
            _apply_remove(composite_key, trait_key)
            removed_ids.append(row.id)
    added_count = CohortMembership.objects.filter(
        id__in=added_ids, state=CohortMembershipState.PENDING_ADD
    ).update(state=CohortMembershipState.APPLIED)
    removed_count, _ = CohortMembership.objects.filter(
        id__in=removed_ids, state=CohortMembershipState.PENDING_REMOVE
    ).delete()
    flagsmith_cohorts_membership_deltas_applied_total.labels(operation="add").inc(
        added_count
    )
    flagsmith_cohorts_membership_deltas_applied_total.labels(operation="remove").inc(
        removed_count
    )
    logger.info(
        "membership.applied",
        cohort__id=cohort.id,
        environment__id=cohort.environment_id,
        adds__count=added_count,
        removes__count=removed_count,
    )
    return len(batch)


def _apply_add(
    composite_key: str,
    identifier: str,
    environment_api_key: str,
    trait_key: str,
) -> None:
    for _ in range(COHORT_MEMBERSHIP_APPLY_MAX_ATTEMPTS):
        document = identity_wrapper.get_item(composite_key)
        system_traits = document.get("system_traits") if document else None
        if isinstance(system_traits, dict) and system_traits.get(trait_key) is True:
            return
        try:
            if document is None:
                identity_wrapper.table.put_item(  # type: ignore[union-attr]
                    Item=map_engine_identity_to_identity_document(
                        IdentityModel(
                            identifier=identifier,
                            environment_api_key=environment_api_key,
                            system_traits={trait_key: True},
                        )
                    ),
                    ConditionExpression="attribute_not_exists(composite_key)",
                )
            elif isinstance(system_traits, dict):
                identity_wrapper.table.update_item(  # type: ignore[union-attr]
                    Key={"composite_key": composite_key},
                    UpdateExpression="SET system_traits.#tk = :true",
                    ConditionExpression="attribute_exists(system_traits)",
                    ExpressionAttributeNames={"#tk": trait_key},
                    ExpressionAttributeValues={":true": True},
                )
            else:
                identity_wrapper.table.update_item(  # type: ignore[union-attr]
                    Key={"composite_key": composite_key},
                    UpdateExpression="SET system_traits = :init",
                    # attribute_exists guard: update_item would otherwise
                    # upsert a skeleton document for a deleted identity.
                    ConditionExpression=(
                        "attribute_exists(composite_key)"
                        " AND attribute_not_exists(system_traits)"
                    ),
                    ExpressionAttributeValues={":init": {trait_key: True}},
                )
            return
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
    raise CohortMembershipApplyRaceError(composite_key)


def _apply_remove(composite_key: str, trait_key: str) -> None:
    try:
        identity_wrapper.table.update_item(  # type: ignore[union-attr]
            Key={"composite_key": composite_key},
            UpdateExpression="REMOVE system_traits.#tk",
            # Failing this condition covers every no-op case at once:
            # missing document, missing map, or trait already absent.
            ConditionExpression="attribute_exists(system_traits.#tk)",
            ExpressionAttributeNames={"#tk": trait_key},
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
