import structlog
from django.utils import timezone

from app_analytics.types import KnownSDK
from environments.models import Environment

logger = structlog.get_logger("onboarding")


def record_environment_first_evaluation(
    environment: Environment,
    sdk_label: KnownSDK,
) -> None:
    """Mark this environment as having been evaluated by a client SDK."""
    log = logger.bind(
        environment__id=environment.id,
        project__id=environment.project_id,
        organisation__id=environment.project.organisation_id,
        sdk__label=sdk_label,
    )

    if environment.first_evaluated_at is not None:
        log.info("environment.already_evaluated")
        return

    environment.first_evaluated_at = timezone.now()
    environment.first_evaluated_sdk_label = sdk_label
    environment.save(update_fields=["first_evaluated_at", "first_evaluated_sdk_label"])

    Environment.write_environment_documents(environment_id=environment.id)

    log.info("environment.first_evaluated")
