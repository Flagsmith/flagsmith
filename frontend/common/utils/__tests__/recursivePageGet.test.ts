import { recursivePageGet } from 'common/utils/recursivePageGet'

describe('recursivePageGet', () => {
  it('follows next links, concatenating the pages', async () => {
    // Given
    const baseQuery = jest
      .fn()
      .mockResolvedValueOnce({
        data: {
          count: 3,
          next: 'items/?page=2',
          previous: null,
          results: [1, 2],
        },
      })
      .mockResolvedValueOnce({
        data: { count: 3, next: null, previous: 'items/?page=1', results: [3] },
      })

    // When
    const res = await recursivePageGet<number>('items/?page=1', null, baseQuery)

    // Then
    expect(baseQuery.mock.calls.map(([arg]) => arg)).toEqual([
      { method: 'GET', url: 'items/?page=1' },
      { method: 'GET', url: 'items/?page=2' },
    ])
    expect(res.data?.results).toEqual([1, 2, 3])
  })

  it('returns the error of a failing page', async () => {
    // Given
    const error = { status: 500 }
    const baseQuery = jest
      .fn()
      .mockResolvedValueOnce({
        data: { count: 3, next: 'items/?page=2', previous: null, results: [1] },
      })
      .mockResolvedValueOnce({ error })

    // When
    const res = await recursivePageGet<number>('items/?page=1', null, baseQuery)

    // Then
    expect(res.error).toBe(error)
  })
})
