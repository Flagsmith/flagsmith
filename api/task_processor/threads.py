import time
from threading import Thread

from task_processor.processor import run_next_task


class TaskRunner(Thread):
    def __init__(
        self, *args, main: Thread, sleep_interval_millis: int = 2000, **kwargs
    ):
        super(TaskRunner, self).__init__(*args, **kwargs)
        self.sleep_interval_millis = sleep_interval_millis
        self._main = main

    def run(self) -> None:
        while self._main.is_alive():
            run_next_task()
            time.sleep(self.sleep_interval_millis)
