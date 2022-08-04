import time
from threading import Thread

from task_processor.processor import run_next_task


class TaskRunner(Thread):
    def __init__(self, *args, sleep_interval_millis: int = 2000, **kwargs):
        super(TaskRunner, self).__init__(*args, **kwargs)
        self.sleep_interval_millis = sleep_interval_millis

        self._stopped = False

    def run(self) -> None:
        while not self._stopped:
            run_next_task()
            time.sleep(self.sleep_interval_millis / 1000)

    def stop(self):
        self._stopped = True
