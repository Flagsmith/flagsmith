import logging
import time
from contextvars import ContextVar
from threading import Thread

from django.utils import timezone

from task_processor.processor import run_recurring_tasks, run_tasks

logger = logging.getLogger(__name__)

_stopped = ContextVar("_stopped", default=False)
_last_checked_for_tasks = ContextVar("_last_checked_for_tasks", default=None)


class TaskRunner(Thread):
    def __init__(
        self,
        *args,
        sleep_interval_millis: int = 2000,
        queue_pop_size: int = 1,
        **kwargs,
    ):
        super(TaskRunner, self).__init__(
            *args,
            kwargs={
                "sleep_interval_millis": sleep_interval_millis,
                "queue_pop_size": queue_pop_size,
            },
            **kwargs,
        )

    @staticmethod
    def _target(*_, **kwargs) -> None:
        queue_pop_size = kwargs["queue_pop_size"]
        sleep_interval_seconds = kwargs["sleep_interval_millis"] / 1000

        while not _stopped:
            _last_checked_for_tasks.set(timezone.now())
            run_tasks(queue_pop_size)
            run_recurring_tasks(queue_pop_size)
            time.sleep(sleep_interval_seconds)

    def stop(self):
        _stopped.set(True)
