import AccountStore from 'common/stores/account-store'
import {
  isAllowedWhileBlocked,
  isOrganisationUsage,
  shouldShowOrganisationLimit,
} from 'web/routePaths'

jest.mock('common/stores/account-store', () => ({
  __esModule: true,
  default: { isAdmin: jest.fn() },
}))

const mockIsAdmin = AccountStore.isAdmin as jest.Mock

beforeEach(() => {
  mockIsAdmin.mockReset()
})

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
    isAdmin  | pathname                         | usageDashboardEnabled | shouldShow
    ${true}  | ${'/organisation/7528/usage'}    | ${false}              | ${true}
    ${true}  | ${'/organisation/7528/usage'}    | ${true}               | ${false}
    ${true}  | ${'/organisation/7528/projects'} | ${true}               | ${true}
    ${false} | ${'/organisation/7528/usage'}    | ${false}              | ${false}
    ${false} | ${'/organisation/7528/projects'} | ${true}               | ${false}
  `(
    'admin=$isAdmin, pathname=$pathname, usage dashboard=$usageDashboardEnabled: $shouldShow',
    ({ isAdmin, pathname, shouldShow, usageDashboardEnabled }) => {
      mockIsAdmin.mockReturnValue(isAdmin)
      expect(shouldShowOrganisationLimit(pathname, usageDashboardEnabled)).toBe(
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
