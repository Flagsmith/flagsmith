import {
  getScopeDisplayLabel,
  writeScopeParams,
} from 'components/audit-log/auditLogScopeFilter'

describe('getScopeDisplayLabel', () => {
  it.each`
    scope                                                         | projectName  | label
    ${{ type: 'all' }}                                            | ${undefined} | ${'Everything'}
    ${{ type: 'organisation' }}                                   | ${undefined} | ${'Organisation'}
    ${{ environmentIds: [], projectId: 12, type: 'project' }}     | ${'Website'} | ${'Website'}
    ${{ environmentIds: [3], projectId: 12, type: 'project' }}    | ${'Website'} | ${'Website · 1 environment'}
    ${{ environmentIds: [3, 4], projectId: 12, type: 'project' }} | ${'Website'} | ${'Website · 2 environments'}
    ${{ environmentIds: [], projectId: 12, type: 'project' }}     | ${undefined} | ${'Project'}
  `(
    '$scope.type with $projectName: $label',
    ({ label, projectName, scope }) => {
      expect(getScopeDisplayLabel(scope, projectName)).toBe(label)
    },
  )
})

describe('writeScopeParams', () => {
  it('replaces the scope and keeps the search', () => {
    const params = new URLSearchParams('search=role&project=12&environment=4')
    writeScopeParams(params, { type: 'organisation' })
    expect(params.toString()).toBe('search=role&scope=organisation')
  })
})
