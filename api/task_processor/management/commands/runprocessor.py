import signal
import threading
from argparse import ArgumentParser

from django.core.management import BaseCommand

from task_processor.threads import TaskRunner


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)
        self._stop = False

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--numthreads",
            type=int,
            help="Number of worker threads to run.",
            default=5,
        )

    def handle(self, *args, **options):
        num_threads = options["numthreads"]
        current_thread = threading.current_thread()
        threads = [TaskRunner(main=current_thread) for _ in range(num_threads)]

        for thread in threads:
            thread.start()

        while not self._stop:
            # TODO: add some monitoring here
            continue

    def _exit_gracefully(self, *args):
        self._stop = True
