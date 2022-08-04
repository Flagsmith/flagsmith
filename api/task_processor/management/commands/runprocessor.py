import logging
import signal
import typing
from argparse import ArgumentParser

from django.core.management import BaseCommand

from task_processor.tasks import registered_tasks
from task_processor.threads import TaskRunner

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

        self._threads: typing.List[TaskRunner] = []
        self._monitor_threads = False

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--numthreads",
            type=int,
            help="Number of worker threads to run.",
            default=5,
        )

    def handle(self, *args, **options):
        num_threads = options["numthreads"]
        self._threads.extend([TaskRunner() for _ in range(num_threads)])

        logger.info(
            "Processor starting. Registered tasks are: %s",
            list(registered_tasks.keys()),
        )

        for thread in self._threads:
            thread.start()

        self._monitor_threads = True
        while self._monitor_threads:
            # TODO: add monitoring logic
            continue

        [t.join() for t in self._threads]

    def _exit_gracefully(self, *args):
        self._monitor_threads = False
        for t in self._threads:
            t.stop()
