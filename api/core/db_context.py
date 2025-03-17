import threading

_thread_locals = threading.local()


def enable_read_replicas() -> None:
    _thread_locals.enable_read_replicas = True


def read_replicas_enabled() -> bool:
    return getattr(_thread_locals, "enable_read_replicas", False) is True


def disable_read_replicas() -> None:
    if hasattr(_thread_locals, "enable_read_replicas"):
        del _thread_locals.enable_read_replicas
