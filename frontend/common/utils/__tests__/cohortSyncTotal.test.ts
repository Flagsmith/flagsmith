import {
  clearCohortSyncTotal,
  getCohortSyncProgress,
  saveCohortSyncTotal,
} from 'common/utils/cohortSyncTotal'

const storage = new Map<string, string>()
jest.mock('common/safeLocalStorage', () => ({
  storageGet: (key: string) => storage.get(key) ?? null,
  storageRemove: (key: string) => storage.delete(key),
  storageSet: (key: string, value: string) => storage.set(key, value),
}))

describe('getCohortSyncProgress', () => {
  beforeEach(() => {
    storage.clear()
  })

  it('counts batches applied before the first poll as done', () => {
    // Given
    saveCohortSyncTotal(1, 2, 1100)

    // When
    const progress = getCohortSyncProgress(1, 2, 900)

    // Then
    expect(progress).toEqual({ done: 200, total: 1100 })
  })

  it('never reports a total below the pending count', () => {
    // Given
    saveCohortSyncTotal(1, 2, 100)

    // When
    const progress = getCohortSyncProgress(1, 2, 150)

    // Then
    expect(progress).toEqual({ done: 0, total: 150 })
  })

  it.each`
    description                             | stored                         | version
    ${'nothing was saved'}                  | ${null}                        | ${2}
    ${'an older sync saved the total'}      | ${{ total: 10, version: 1 }}   | ${2}
    ${'the stored value is not JSON'}       | ${'not-json'}                  | ${2}
    ${'the stored value has another shape'} | ${{ total: '10', version: 2 }} | ${2}
  `('returns null when $description', ({ stored, version }) => {
    // Given
    if (stored !== null) {
      storage.set(
        'cohort_sync_total_1',
        typeof stored === 'string' ? stored : JSON.stringify(stored),
      )
    }

    // When
    const progress = getCohortSyncProgress(1, version, 5)

    // Then
    expect(progress).toBeNull()
  })
})

describe('saveCohortSyncTotal', () => {
  beforeEach(() => {
    storage.clear()
  })

  it('saves nothing when the sync queued no work', () => {
    // Given / When
    saveCohortSyncTotal(1, 2, 0)

    // Then
    expect(storage.size).toBe(0)
  })
})

describe('clearCohortSyncTotal', () => {
  beforeEach(() => {
    storage.clear()
  })

  it('removes the total of the finished sync', () => {
    // Given
    saveCohortSyncTotal(1, 2, 100)

    // When
    clearCohortSyncTotal(1, 2)

    // Then
    expect(getCohortSyncProgress(1, 2, 0)).toBeNull()
  })

  it('keeps a newer total while the cohort response is stale', () => {
    // Given
    saveCohortSyncTotal(1, 3, 100)

    // When
    clearCohortSyncTotal(1, 2)

    // Then
    expect(getCohortSyncProgress(1, 3, 40)).toEqual({ done: 60, total: 100 })
  })
})
