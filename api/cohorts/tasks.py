from datetime import timedelta

import structlog
from botocore.exceptions import ClientError
from task_processor.decorators import register_task_handler
from task_processor.exceptions import TaskBackoffError

from cohorts import services
from cohorts.constants import (
    COHORT_MEMBERSHIP_APPLY_MAX_BATCHES_PER_RUN,
    DYNAMODB_THROTTLING_ERROR_CODES,
)
from cohorts.models import Cohort

logger = structlog.get_logger("cohorts")


@register_task_handler(timeout=timedelta(minutes=5))
def apply_cohort_membership_deltas(cohort_id: int) -> None:
    log = logger.bind(cohort__id=cohort_id)
    if (cohort := Cohort.objects.filter(id=cohort_id).first()) is None:
        log.info("membership.apply.skipped", reason="cohort_missing")
        return
    try:
        for _ in range(COHORT_MEMBERSHIP_APPLY_MAX_BATCHES_PER_RUN):
            if not services.apply_pending_memberships(cohort):
                if cohort.deletion_requested_at is not None:
                    services.finalise_cohort_deletion(cohort)
                return
    except ClientError as exc:
        if exc.response["Error"]["Code"] in DYNAMODB_THROTTLING_ERROR_CODES:
            log.warning("membership.apply.throttled")
            raise TaskBackoffError() from exc
        raise
    # Still pending after this run's batch cap; continue in a fresh task run.
    apply_cohort_membership_deltas.delay(kwargs={"cohort_id": cohort_id})
