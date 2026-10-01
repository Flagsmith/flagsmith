import { fetchAllPages } from 'common/utils/fetchAllPages'

const page = (results: number[], next?: string) => ({
  data: { next, results },
})

describe('fetchAllPages', () => {
  it('follows next until the last page', async () => {
    const fetchPage = jest
      .fn()
      .mockResolvedValueOnce(page([1, 2], '?page=2'))
      .mockResolvedValueOnce(page([3]))

    expect(await fetchAllPages(fetchPage)).toEqual({ data: [1, 2, 3] })
    expect(fetchPage.mock.calls).toEqual([[1], [2]])
  })

  it('returns the error of a failed page instead of a partial list', async () => {
    const error = { status: 500 }
    const fetchPage = jest
      .fn()
      .mockResolvedValueOnce(page([1], '?page=2'))
      .mockResolvedValueOnce({ error })

    expect(await fetchAllPages(fetchPage)).toEqual({ error })
  })
})
