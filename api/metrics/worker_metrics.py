<<<<<<< HEAD
from pathlib import Path
from typing import Iterable
import prometheus_client


PROC_SELF_STATUS_PATH = Path("/proc/self/status")
MAX_RSS_KB_TO_BYTES = 1024
MAX_RSS_STATUS_FIELD = "VmHWM"

flagsmith_worker_rss_bytes = prometheus_client.Gauge(
    "flagsmith_worker_rss_bytes",
    "Resident Set Size (RSS) of the worker process in bytes.",
    ["pid"],
    
)

def get_current_process_max_rss_bytes() -> int | None:
    try:
        proc_status_lines = PROC_SELF_STATUS_PATH.read_text(
            encoding="utf-8"
        ).splitlines()
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return None

    max_rss_kb = _get_proc_status_memory_kb(proc_status_lines, MAX_RSS_STATUS_FIELD)
    if max_rss_kb is None:
        return None

    return max_rss_kb * MAX_RSS_KB_TO_BYTES


def _get_proc_status_memory_kb(
    proc_status_lines: Iterable[str],
    field_name: str,
) -> int | None:
    for line in proc_status_lines:
        name, separator, value = line.strip().partition(":")
        if separator and name == field_name:
            return _parse_proc_status_memory_kb(value)

    return None


def _parse_proc_status_memory_kb(value: str) -> int | None:
    parts = value.split()
    if len(parts) != 2:
        return None

    memory_kb_text, unit = parts
    if unit != "kB":
        return None

    try:
        memory_kb = int(memory_kb_text)
    except ValueError:
        return None

    if memory_kb < 0:
        return None

    return memory_kb

=======
import prometheus_client

flagsmith_worker_rss_bytes = prometheus_client.Gauge(
    "flagsmith_worker_rss_bytes",
    "Resident Set Size (RSS) of the worker process in bytes.",
    ["pid"]
)
>>>>>>> d7ea9dc2 (created worker metric Prometheus gauge)
