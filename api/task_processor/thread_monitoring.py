import logging

from pydantic import BaseModel

THREAD_COUNTS_FILE_PATH = "/tmp/task-processor-thread-counts.json"

logger = logging.getLogger(__name__)


class ThreadCounts(BaseModel):
    running: int
    expected: int


def write_thread_counts(thread_counts: ThreadCounts) -> None:
    with open(THREAD_COUNTS_FILE_PATH, "w+") as f:
        f.write(thread_counts.json())


def get_thread_counts() -> ThreadCounts:
    with open(THREAD_COUNTS_FILE_PATH, "r") as f:
        return ThreadCounts.parse_raw(f.read())
