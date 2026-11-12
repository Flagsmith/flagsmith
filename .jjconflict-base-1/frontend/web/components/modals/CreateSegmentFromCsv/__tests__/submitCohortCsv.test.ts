import { submitCohortCsv } from 'components/modals/CreateSegmentFromCsv/submitCohortCsv'

describe('submitCohortCsv', () => {
  test('first submit creates the cohort, records it, then syncs', async () => {
    const createCohort = jest.fn().mockResolvedValue({ id: 7 })
    const syncCsv = jest.fn().mockResolvedValue({ added: 3 })
    const onCohortCreated = jest.fn()

    const result = await submitCohortCsv({
      createCohort,
      createdCohort: null,
      formKey: 'a',
      onCohortCreated,
      syncCsv,
    })

    expect(createCohort).toHaveBeenCalledTimes(1)
    expect(onCohortCreated).toHaveBeenCalledWith({ formKey: 'a', id: 7 })
    expect(syncCsv).toHaveBeenCalledWith(7)
    expect(result).toEqual({ added: 3 })
  })

  test('retry with an unchanged form reuses the cohort and only syncs', async () => {
    const createCohort = jest.fn()
    const syncCsv = jest.fn().mockResolvedValue({ added: 3 })
    const onCohortCreated = jest.fn()

    await submitCohortCsv({
      createCohort,
      createdCohort: { formKey: 'a', id: 7 },
      formKey: 'a',
      onCohortCreated,
      syncCsv,
    })

    expect(createCohort).not.toHaveBeenCalled()
    expect(onCohortCreated).not.toHaveBeenCalled()
    expect(syncCsv).toHaveBeenCalledWith(7)
  })

  test('retry after editing the form creates a new cohort instead of reusing it', async () => {
    const createCohort = jest.fn().mockResolvedValue({ id: 9 })
    const syncCsv = jest.fn().mockResolvedValue({ added: 1 })
    const onCohortCreated = jest.fn()

    await submitCohortCsv({
      createCohort,
      createdCohort: { formKey: 'a', id: 7 },
      formKey: 'b',
      onCohortCreated,
      syncCsv,
    })

    expect(createCohort).toHaveBeenCalledTimes(1)
    expect(onCohortCreated).toHaveBeenCalledWith({ formKey: 'b', id: 9 })
    expect(syncCsv).toHaveBeenCalledWith(9)
  })

  test('a failed sync still records the created cohort for retry', async () => {
    const createCohort = jest.fn().mockResolvedValue({ id: 7 })
    const syncCsv = jest.fn().mockRejectedValue(new Error('sync failed'))
    const onCohortCreated = jest.fn()

    await expect(
      submitCohortCsv({
        createCohort,
        createdCohort: null,
        formKey: 'a',
        onCohortCreated,
        syncCsv,
      }),
    ).rejects.toThrow('sync failed')

    expect(onCohortCreated).toHaveBeenCalledWith({ formKey: 'a', id: 7 })
  })
})
