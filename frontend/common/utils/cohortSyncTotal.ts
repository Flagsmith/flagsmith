import { storageGet, storageRemove, storageSet } from 'common/safeLocalStorage'

type StoredCohortSyncTotal = {
  total: number
  version: number
}

export type CohortSyncProgress = {
  done: number
  total: number
}

const storageKey = (cohortId: number) => `cohort_sync_total_${cohortId}`

// The applier starts before the dashboard first polls, so only the sync
// response knows how much work a synchronisation queued.
export function saveCohortSyncTotal(
  cohortId: number,
  version: number,
  total: number,
): void {
  if (!total) {
    return
  }
  storageSet(storageKey(cohortId), JSON.stringify({ total, version }))
}

function getStoredCohortSyncTotal(
  cohortId: number,
): StoredCohortSyncTotal | null {
  try {
    const stored = JSON.parse(storageGet(storageKey(cohortId)) ?? 'null')
    return typeof stored?.total === 'number' &&
      typeof stored?.version === 'number'
      ? stored
      : null
  } catch {
    return null
  }
}

// A total saved by an older synchronisation, or in another browser, is
// unknown: callers fall back to the pending count alone.
export function getCohortSyncProgress(
  cohortId: number,
  version: number,
  pendingCount: number,
): CohortSyncProgress | null {
  const stored = getStoredCohortSyncTotal(cohortId)
  if (stored?.version !== version) {
    return null
  }
  const total = Math.max(stored.total, pendingCount)
  return { done: total - pendingCount, total }
}

export function clearCohortSyncTotal(cohortId: number, version: number): void {
  if (getStoredCohortSyncTotal(cohortId)?.version === version) {
    storageRemove(storageKey(cohortId))
  }
}
