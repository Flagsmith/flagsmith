import logging
import time
import traceback
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
            self.run_iteration()
            time.sleep(self.sleep_interval_millis / 1000)

    def run_iteration(self) -> None:
        try:
            run_tasks(self.queue_pop_size)
            run_recurring_tasks(self.queue_pop_size)
        except Exception as e:
            # To prevent task threads from dying if they get an error retrieving the tasks from the
            # database this will allow the thread to continue trying to retrieve tasks if it can
            # successfully re-establish a connection to the database.
            # TODO: is this also what is causing tasks to get stuck as locked? Can we unlock
            #  tasks here?

            logger.error("Received error retrieving tasks: %s.", e)
            logger.debug(traceback.format_exc())

    def stop(self):
        self._stopped = True
