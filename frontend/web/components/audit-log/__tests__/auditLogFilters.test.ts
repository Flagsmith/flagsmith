import {
  hasActiveAuditLogFilters,
  parseAuditLogFilters,
  serialiseAuditLogFilters,
  toOrganisationAuditLogParams,
} from 'components/audit-log/auditLogFilters'

describe('toOrganisationAuditLogParams', () => {
  it.each`
    search       | sent
    ${''}        | ${undefined}
    ${'ch'}      | ${undefined}
    ${'  ch  '}  | ${undefined}
    ${'che'}     | ${'che'}
    ${' check '} | ${'check'}
  `('search "$search" sends $sent', ({ search, sent }) => {
    expect(toOrganisationAuditLogParams({ search }).search).toBe(sent)
  })
})

describe('URL round trip', () => {
  it.each`
    search
    ${''}
    ${'checkout'}
  `('"$search" survives serialise then parse', ({ search }) => {
    expect(parseAuditLogFilters(serialiseAuditLogFilters({ search }))).toEqual({
      search,
    })
  })

  it('ignores parameters it does not know', () => {
    expect(
      parseAuditLogFilters(new URLSearchParams('project=12&search=role')),
    ).toEqual({ search: 'role' })
  })
})

describe('hasActiveAuditLogFilters', () => {
  it.each`
    search   | active
    ${''}    | ${false}
    ${'  '}  | ${false}
    ${'ch'}  | ${false}
    ${'che'} | ${true}
  `('"$search": $active', ({ active, search }) => {
    expect(hasActiveAuditLogFilters({ search })).toBe(active)
  })
})
