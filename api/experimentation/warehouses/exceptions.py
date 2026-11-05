class UnsupportedWarehouseOperation(Exception):
    """Raised before any side effect when a warehouse type lacks an operation."""


class DeliveryConfigError(Exception):
    """The connection's stored configuration cannot be used to reach the
    warehouse."""


class MissingEventsTableError(Exception):
    """The configured database has no events table to deliver into."""


class EventsTableSchemaMismatchError(Exception):
    """The events table lacks a column delivery writes, or has the wrong type."""


class EventsTablePermissionError(Exception):
    """The configured user cannot both read and insert into the events table."""
