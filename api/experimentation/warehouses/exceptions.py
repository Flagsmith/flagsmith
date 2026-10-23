class UnsupportedWarehouseOperation(Exception):
    """Raised before any side effect when a warehouse type lacks an operation."""


class DeliveryConfigError(Exception):
    """The connection's stored configuration cannot be used to reach the
    warehouse."""


class MissingEventsTableError(Exception):
    """The configured database has no events table to deliver into."""
