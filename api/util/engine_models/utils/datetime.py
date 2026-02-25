from datetime import datetime, timezone


def utcnow_with_tz() -> datetime:
    return datetime.now(tz=timezone.utc)
