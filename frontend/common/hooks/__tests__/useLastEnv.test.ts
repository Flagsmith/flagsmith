import { parseLastEnv } from 'common/hooks/useLastEnv'

describe('parseLastEnv', () => {
  it('reads what usePageTracking wrote', () => {
    const raw = JSON.stringify({ environmentId: 'abc', orgId: 1, projectId: 2 })
    expect(parseLastEnv(raw)).toEqual({
      environmentId: 'abc',
      orgId: 1,
      projectId: 2,
    })
  })

  it.each([null, '', 'not json', '{'])('survives %p', (raw) => {
    expect(parseLastEnv(raw)).toBeNull()
  })
})
