import logging

from audit.models import AuditLog

logger = logging.getLogger(__name__)


def handle_skipped_signals(f):
    def wrapper(*args, **kwargs):
        try:
            audit_log = args[1] if len(args) >= 2 else kwargs["instance"]
            if not isinstance(audit_log, AuditLog):
                raise TypeError("Must be AuditLog instance.")
            skip_signals = audit_log.skip_signals.split(",")
            if f.__name__ not in skip_signals:
                return f(*args, **kwargs)

            logger.debug("Skipping signal %s." % f.__name__)
            return None
        except (KeyError, AttributeError):
            return f(*args, **kwargs)

    return wrapper
