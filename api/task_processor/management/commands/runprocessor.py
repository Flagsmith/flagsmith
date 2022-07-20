import threading
from argparse import ArgumentParser

from django.core.management import BaseCommand

from task_processor.threads import TaskRunner


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--numthreads",
            type=int,
            help="Number of worker threads to run.",
            default=5,
        )

    def handle(self, *args, **options):
        num_threads = options["numthreads"]
        threads = [
            TaskRunner(main=threading.current_thread()) for _ in range(num_threads)
        ]

        for thread in threads:
            thread.start()
