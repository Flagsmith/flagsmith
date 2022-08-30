import logging
import sys

from django.core.management import BaseCommand

from task_processor.thread_monitoring import get_unhealthy_thread_names

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        if get_unhealthy_thread_names():
            sys.exit("Task processor has unhealthy threads.")

        logger.info("Task processor has no unhealthy threads.")
        sys.exit(0)
