import { submitCohortCsv } from 'components/modals/CreateSegmentFromCsv/submitCohortCsv'

describe('submitCohortCsv', () => {
  test('first submit creates the cohort, records it, then syncs', async () => {
    const createCohort = jest.fn().mockResolvedValue({ id: 7 })
    const syncCsv = jest.fn().mockResolvedValue({ added: 3 })
    const onCohortCreated = jest.fn()

    const result = await submitCohortCsv({
      createCohort,
      existingCohortId: null,
      onCohortCreated,
      syncCsv,
    })

    expect(createCohort).toHaveBeenCalledTimes(1)
    expect(onCohortCreated).toHaveBeenCalledWith(7)
    expect(syncCsv).toHaveBeenCalledWith(7)
    expect(result).toEqual({ added: 3 })
  })

  test('retry with an existing cohort skips creation and only syncs', async () => {
    const createCohort = jest.fn()
    const syncCsv = jest.fn().mockResolvedValue({ added: 3 })
    const onCohortCreated = jest.fn()

    await submitCohortCsv({
      createCohort,
      existingCohortId: 7,
      onCohortCreated,
      syncCsv,
    })

    expect(createCohort).not.toHaveBeenCalled()
    expect(onCohortCreated).not.toHaveBeenCalled()
    expect(syncCsv).toHaveBeenCalledWith(7)
  })

  test('a failed sync still records the created cohort for retry', async () => {
    const createCohort = jest.fn().mockResolvedValue({ id: 7 })
    const syncCsv = jest.fn().mockRejectedValue(new Error('sync failed'))
    const onCohortCreated = jest.fn()

    await expect(
      submitCohortCsv({
        createCohort,
        existingCohortId: null,
        onCohortCreated,
        syncCsv,
      }),
    ).rejects.toThrow('sync failed')

    expect(onCohortCreated).toHaveBeenCalledWith(7)
  })
})
