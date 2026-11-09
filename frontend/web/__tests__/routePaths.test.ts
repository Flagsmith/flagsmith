import {
  isAllowedWhileBlocked,
  isOrganisationUsage,
  shouldShowOrganisationLimit,
} from 'web/routePaths'

// App renders <Blocked /> wherever this is false, so a wrong answer either
// locks a blocked organisation out, or lets it back in.
describe('isAllowedWhileBlocked', () => {
  it.each`
    pathname                                 | allowed
    ${'/organisation/7528/usage'}            | ${true}
    ${'/organisations'}                      | ${true}
    ${'/organisation/7528/projects'}         | ${false}
    ${'/organisation/7528/settings'}         | ${false}
    ${'/organisation-settings'}              | ${false}
    ${'/project/1/environment/abc/features'} | ${false}
    ${'/account'}                            | ${false}
  `(
    '$pathname is reachable while blocked: $allowed',
    ({ allowed, pathname }) => {
      expect(isAllowedWhileBlocked(pathname)).toBe(allowed)
    },
  )

  // Allowed by pattern, not by prefix.
  it('does not open anything nested under the usage page', () => {
    expect(isAllowedWhileBlocked('/organisation/7528/usage/breakdown')).toBe(
      false,
    )
  })
})

describe('shouldShowOrganisationLimit', () => {
  it.each`
    isAdmin  | hasOwnQuotaBanner | shouldShow
    ${true}  | ${false}          | ${true}
    ${true}  | ${true}           | ${false}
    ${false} | ${false}          | ${false}
    ${false} | ${true}           | ${false}
  `(
    'admin=$isAdmin, own quota banner=$hasOwnQuotaBanner: $shouldShow',
    ({ hasOwnQuotaBanner, isAdmin, shouldShow }) => {
      expect(shouldShowOrganisationLimit(isAdmin, hasOwnQuotaBanner)).toBe(
        shouldShow,
      )
    },
  )
})

// App hides its app-wide quota banner here, where the page has its own.
describe('isOrganisationUsage', () => {
  it.each`
    pathname                             | isUsage
    ${'/organisation/7528/usage'}        | ${true}
    ${'/organisation/7528/projects'}     | ${false}
    ${'/organisation/7528/usage/charts'} | ${false}
    ${'/organisations'}                  | ${false}
  `('$pathname is the usage page: $isUsage', ({ isUsage, pathname }) => {
    expect(isOrganisationUsage(pathname)).toBe(isUsage)
  })
})
