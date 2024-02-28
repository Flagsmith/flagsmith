import logging
import sys

from django.core.management import BaseCommand

from task_processor.thread_monitoring import get_thread_counts

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        thread_counts = get_thread_counts()

        if thread_counts.running != thread_counts.expected:
            sys.exit(
                "Processor is running %d threads, but expected %d"
                % (thread_counts.running, thread_counts.expected)
            )

        sys.exit(0)
