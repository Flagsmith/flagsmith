import { getAuditLogErrorKind } from 'components/audit-log/auditLogError'

describe('getAuditLogErrorKind', () => {
  it.each`
    name                     | error                                                   | kind
    ${'not an admin'}        | ${{ status: 403 }}                                      | ${'forbidden'}
    ${'not a member'}        | ${{ status: 404 }}                                      | ${'forbidden'}
    ${'search timed out'}    | ${{ data: { code: 'statement_timeout' }, status: 503 }} | ${'timeout'}
    ${'other 503'}           | ${{ data: { code: 'maintenance' }, status: 503 }}       | ${'unknown'}
    ${'server error'}        | ${{ status: 500 }}                                      | ${'unknown'}
    ${'network failure'}     | ${{ error: 'Failed to fetch', status: 'FETCH_ERROR' }}  | ${'unknown'}
    ${'not an error object'} | ${'boom'}                                               | ${'unknown'}
  `('$name: $kind', ({ error, kind }) => {
    expect(getAuditLogErrorKind(error)).toBe(kind)
  })
})
