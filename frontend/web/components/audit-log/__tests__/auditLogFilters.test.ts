import {
  AuditLogFilters,
  hasActiveAuditLogFilters,
  parseAuditLogFilters,
  serialiseAuditLogFilters,
  showsClearAll,
  toOrganisationAuditLogParams,
} from 'components/audit-log/auditLogFilters'

const filters = (
  scope: AuditLogFilters['scope'],
  search = '',
): AuditLogFilters => ({ scope, search })

describe('toOrganisationAuditLogParams', () => {
  it('sends nothing for all events with no search', () => {
    expect(toOrganisationAuditLogParams(filters({ type: 'all' }))).toEqual({})
  })

  // The API answers 400 to organisation level plus project or environments.
  it('never sends project or environments with organisation events only', () => {
    expect(
      toOrganisationAuditLogParams(filters({ type: 'organisation' })),
    ).toEqual({ is_organisation_level: true })
  })

  it('sends the project and its environments', () => {
    expect(
      toOrganisationAuditLogParams(
        filters({ environmentIds: [4, 5], projectId: 12, type: 'project' }),
      ),
    ).toEqual({ environments: [4, 5], project: 12 })
  })

  it('leaves environments out when none are picked', () => {
    expect(
      toOrganisationAuditLogParams(
        filters({ environmentIds: [], projectId: 12, type: 'project' }),
      ),
    ).toEqual({ environments: undefined, project: 12 })
  })

  it.each`
    search       | sent
    ${'ch'}      | ${undefined}
    ${'  ch  '}  | ${undefined}
    ${'che'}     | ${'che'}
    ${' check '} | ${'check'}
  `('search "$search" sends $sent', ({ search, sent }) => {
    expect(
      toOrganisationAuditLogParams(filters({ type: 'all' }, search)).search,
    ).toBe(sent)
  })

  it('caps a long search at the 256 characters the API accepts', () => {
    expect(
      toOrganisationAuditLogParams(filters({ type: 'all' }, 'a'.repeat(300)))
        .search,
    ).toBe('a'.repeat(256))
  })

  it('sends nothing when the capped search is too short once trimmed', () => {
    expect(
      toOrganisationAuditLogParams(
        filters({ type: 'all' }, `ab${' '.repeat(254)}c`),
      ).search,
    ).toBeUndefined()
  })

  it('never cuts an emoji in half at the cap', () => {
    expect(
      toOrganisationAuditLogParams(
        filters({ type: 'all' }, `${'a'.repeat(255)}😀b`),
      ).search,
    ).toBe(`${'a'.repeat(255)}😀`)
  })
})

describe('URL round trip', () => {
  it.each`
    name                  | value
    ${'all events'}       | ${filters({ type: 'all' })}
    ${'organisation'}     | ${filters({ type: 'organisation' }, 'role')}
    ${'project'}          | ${filters({ environmentIds: [], projectId: 12, type: 'project' })}
    ${'project and envs'} | ${filters({ environmentIds: [4, 5], projectId: 12, type: 'project' }, 'checkout')}
  `('$name survives serialise then parse', ({ value }) => {
    expect(parseAuditLogFilters(serialiseAuditLogFilters(value))).toEqual(value)
  })

  it('prefers a project over scope=organisation in a hand-edited URL', () => {
    expect(
      parseAuditLogFilters(
        new URLSearchParams('scope=organisation&project=12&environment=4'),
      ).scope,
    ).toEqual({ environmentIds: [4], projectId: 12, type: 'project' })
  })

  it('ignores ids that are not positive integers', () => {
    expect(
      parseAuditLogFilters(new URLSearchParams('project=abc&environment=4'))
        .scope,
    ).toEqual({ type: 'all' })
  })

  it('drops environment ids that are not positive integers', () => {
    expect(
      parseAuditLogFilters(
        new URLSearchParams('project=12&environment=abc&environment=4'),
      ).scope,
    ).toEqual({ environmentIds: [4], projectId: 12, type: 'project' })
  })

  it('counts a repeated environment once', () => {
    expect(
      parseAuditLogFilters(
        new URLSearchParams('project=12&environment=4&environment=4'),
      ).scope,
    ).toEqual({ environmentIds: [4], projectId: 12, type: 'project' })
  })
})

describe('filter state', () => {
  // Organisation with no search is a filter, but the scope pill clears it
  // itself, so Clear all stays hidden.
  it.each`
    search   | scope                       | active   | clearAll
    ${''}    | ${{ type: 'all' }}          | ${false} | ${false}
    ${'  '}  | ${{ type: 'all' }}          | ${false} | ${false}
    ${'ch'}  | ${{ type: 'all' }}          | ${false} | ${false}
    ${'che'} | ${{ type: 'all' }}          | ${true}  | ${true}
    ${''}    | ${{ type: 'organisation' }} | ${true}  | ${false}
    ${'che'} | ${{ type: 'organisation' }} | ${true}  | ${true}
  `('"$search" with $scope.type', ({ active, clearAll, scope, search }) => {
    expect(hasActiveAuditLogFilters({ scope, search })).toBe(active)
    expect(showsClearAll({ scope, search })).toBe(clearAll)
  })
})
