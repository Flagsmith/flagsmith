import { WarehouseConnectionStatus } from 'common/types/responses'

export const WAREHOUSE_POLL_INTERVAL_MS = 60000

// Poll until the warehouse has received its first event.
export const getWarehousePollingInterval = (
  status: WarehouseConnectionStatus | undefined,
): number =>
  status === 'created' || status === 'pending_connection'
    ? WAREHOUSE_POLL_INTERVAL_MS
    : 0
