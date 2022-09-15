import logging

from task_processor.decorators import register_task_handler
from task_processor.models import HealthCheckModel

logger = logging.getLogger(__name__)


@register_task_handler()
def create_health_check_model(health_check_model_uuid: str):
    logger.info("Creating health check model.")
    HealthCheckModel.objects.create(uuid=health_check_model_uuid)
