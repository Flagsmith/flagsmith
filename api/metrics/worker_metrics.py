try:
    import resource
except ImportError:  # pragma: no cover - resource is Unix-only
    resource = None  # type: ignore[assignment]


MAX_RSS_KIB_TO_BYTES = 1024


def get_current_process_max_rss_bytes() -> int | None:
    if resource is None or not hasattr(resource, "RUSAGE_SELF"):
        return None

    try:
        max_rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        if max_rss_kib < 0:
            return None
        return max_rss_kib * MAX_RSS_KIB_TO_BYTES
    except (AttributeError, OSError, TypeError, ValueError):
        return None
