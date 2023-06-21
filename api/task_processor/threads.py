import logging
import time
from threading import Thread

from django.utils import timezone

from task_processor.processor import run_recurring_tasks, run_tasks

logger = logging.getLogger(__name__)


class TaskRunner(Thread):
    def __init__(
        self,
        *args,
        sleep_interval_millis: int = 2000,
        queue_pop_size: int = 1,
        **kwargs,
    ):
        super(TaskRunner, self).__init__(*args, **kwargs)
        self.sleep_interval_millis = sleep_interval_millis
        self.queue_pop_size = queue_pop_size
        self.last_checked_for_tasks = None

        self._stopped = False

    def run(self) -> None:
        while not self._stopped:
            self.last_checked_for_tasks = timezone.now()
            try:
                run_tasks(self.queue_pop_size)
            except Exception as e:
                logger.exception(e)
            run_recurring_tasks(self.queue_pop_size)
            time.sleep(self.sleep_interval_millis / 1000)

    def stop(self):
        self._stopped = True
