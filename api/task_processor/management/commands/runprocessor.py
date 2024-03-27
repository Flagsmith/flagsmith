import logging
import signal
import time
import typing
from argparse import ArgumentParser
from datetime import timedelta

from django.core.management import BaseCommand
from django.utils import timezone

from task_processor.task_registry import registered_tasks
from task_processor.thread_monitoring import ThreadCounts, write_thread_counts
from task_processor.threads import TaskRunner

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

        self._threads: typing.List[TaskRunner] = []
        self._monitor_threads = True

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--numthreads",
            type=int,
            help="Number of worker threads to run.",
            default=5,
        )
        parser.add_argument(
            "--sleepintervalms",
            type=int,
            help="Number of millis each worker waits before checking for new tasks",
            default=2000,
        )
        parser.add_argument(
            "--graceperiodms",
            type=int,
            help="Number of millis before running task is considered 'stuck'.",
            default=20000,
        )
        parser.add_argument(
            "--queuepopsize",
            type=int,
            help="Number of tasks each worker will pop from the queue on each cycle.",
            default=10,
        )

    def handle(self, *args, **options):
        num_threads = options["numthreads"]
        sleep_interval_ms = options["sleepintervalms"]
        grace_period_ms = options["graceperiodms"]
        queue_pop_size = options["queuepopsize"]

        logger.debug(
            "Running task processor with args: %s",
            ",".join([f"{k}={v}" for k, v in options.items()]),
        )

        logger.info(
            "Processor starting. Registered tasks are: %s",
            list(registered_tasks.keys()),
        )

        self._spawn_threads(num_threads, sleep_interval_ms, queue_pop_size)

        while self._monitor_threads:
            time.sleep(1)
            if unhealthy_threads := self._get_unhealthy_threads(
                ms_before_unhealthy=grace_period_ms + sleep_interval_ms
            ):
                num_unhealthy_threads = len(unhealthy_threads)

                # remove the unhealthy threads from the list and spawn new ones in their place
                for t in unhealthy_threads:
                    t.stop()
                    self._threads.remove(t)

                self._spawn_threads(
                    num_unhealthy_threads, sleep_interval_ms, queue_pop_size
                )

                logger.debug("Now running %d threads", len(self._threads))

            write_thread_counts(
                ThreadCounts(running=len(self._threads), expected=num_threads)
            )

        [t.join() for t in self._threads]

    def _exit_gracefully(self, *args):
        self._monitor_threads = False
        for t in self._threads:
            t.stop()

    def _get_unhealthy_threads(
        self, ms_before_unhealthy: int
    ) -> typing.List[TaskRunner]:
        unhealthy_threads = []
        healthy_threshold = timezone.now() - timedelta(milliseconds=ms_before_unhealthy)

        for thread in self._threads:
            if (
                not thread.is_alive()
                or not thread.last_checked_for_tasks
                or thread.last_checked_for_tasks < healthy_threshold
            ):
                logger.debug(
                    "Thread status report. is_alive: %r. last_checked_for_tasks: %s.",
                    thread.is_alive(),
                    thread.last_checked_for_tasks,
                )
                unhealthy_threads.append(thread)
        return unhealthy_threads

    def _spawn_threads(
        self, n: int, sleep_interval_ms: int, queue_pop_size: int
    ) -> None:
        logger.info("Starting %d worker threads.", n)

        self._threads.extend(
            [
                TaskRunner(
                    sleep_interval_millis=sleep_interval_ms,
                    queue_pop_size=queue_pop_size,
                )
                for _ in range(n)
            ]
        )

        for thread in self._threads:
            thread.start()
