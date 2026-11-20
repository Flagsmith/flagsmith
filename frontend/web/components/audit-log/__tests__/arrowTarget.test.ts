import { getArrowTarget } from 'components/audit-log/OrganisationAuditLogFilters/ScopeCard/arrowTarget'

describe('getArrowTarget', () => {
  it.each`
    key             | index | target
    ${'ArrowRight'} | ${0}  | ${1}
    ${'ArrowDown'}  | ${2}  | ${0}
    ${'ArrowLeft'}  | ${0}  | ${2}
    ${'ArrowUp'}    | ${1}  | ${0}
    ${'Enter'}      | ${1}  | ${null}
  `('$key from $index of 3 → $target', ({ index, key, target }) => {
    expect(getArrowTarget(key, index, 3)).toBe(target)
  })
})
