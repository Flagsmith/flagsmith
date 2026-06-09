import { WarehouseConnectionStatus } from 'common/types/responses'

export const WAREHOUSE_POLL_INTERVAL_MS = 60000

// RTK Query treats a pollingInterval of 0 as "do not poll". We only poll while
// the backend is waiting for the first event to land in the warehouse.
export const getWarehousePollingInterval = (
  status: WarehouseConnectionStatus | undefined,
): number => (status === 'pending_connection' ? WAREHOUSE_POLL_INTERVAL_MS : 0)
