import { WarehouseConnectionStatus } from 'common/types/responses'

export const WAREHOUSE_POLL_INTERVAL_MS = 60000

// RTK Query treats a pollingInterval of 0 as "do not poll". We poll until the
// warehouse has received its first event, whether the connection is freshly
// created or a test event is on its way.
export const getWarehousePollingInterval = (
  status: WarehouseConnectionStatus | undefined,
): number =>
  status === 'created' || status === 'pending_connection'
    ? WAREHOUSE_POLL_INTERVAL_MS
    : 0
