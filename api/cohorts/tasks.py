from datetime import timedelta

import structlog
from botocore.exceptions import ClientError
from task_processor.decorators import register_task_handler
from task_processor.exceptions import TaskBackoffError

from cohorts import services
from cohorts.models import Cohort, CohortMembership, CohortMembershipState

logger = structlog.get_logger("cohorts")


@register_task_handler(timeout=timedelta(minutes=5))
def apply_cohort_membership_deltas(cohort_id: int) -> None:
    log = logger.bind(cohort__id=cohort_id)
    if (cohort := Cohort.objects.filter(id=cohort_id).first()) is None:
        log.info("membership.apply.skipped", reason="cohort_missing")
        return
    if not (
        cohort.environment.project.enable_dynamo_db
        and services.identity_wrapper.is_enabled
    ):
        log.info("membership.apply.skipped", reason="not_edge")
        return
    try:
        services.apply_pending_memberships(cohort)
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ProvisionedThroughputExceededException":
            log.warning("membership.apply.throttled")
            raise TaskBackoffError() from exc
        raise
    if CohortMembership.objects.filter(
        cohort=cohort,
        state__in=[
            CohortMembershipState.PENDING_ADD,
            CohortMembershipState.PENDING_REMOVE,
        ],
    ).exists():
        apply_cohort_membership_deltas.delay(kwargs={"cohort_id": cohort_id})
