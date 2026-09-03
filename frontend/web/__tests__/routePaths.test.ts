import { isAllowedWhileBlocked } from 'web/routePaths'

// App renders <Blocked /> for a blocked organisation on everything this
// returns false for, so a wrong answer here either locks them out of the page
// that explains the block or lets them back into the app.
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

  // The usage route is allowed by pattern, not by prefix.
  it('does not open anything nested under the usage page', () => {
    expect(isAllowedWhileBlocked('/organisation/7528/usage/breakdown')).toBe(
      false,
    )
  })
})
