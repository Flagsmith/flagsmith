import {
  bannerStateOf,
  NO_BANNER_FLAGS,
} from 'components/pages/usage/bannerState'
import { OverLimit } from 'components/pages/usage/overLimit'

const over: OverLimit = { crossedOn: '2 Aug', limit: 100000, overBy: 50000 }

const organisation = (values = {}) => ({ ...NO_BANNER_FLAGS, ...values })

describe('bannerStateOf', () => {
  it('shows nothing under the limit and unrestricted', () => {
    expect(bannerStateOf(organisation(), undefined)).toBeUndefined()
  })

  // The block outlives the overage, so restriction wins even with none.
  it.each`
    values                             | flagsPaused
    ${{ block_access_to_admin: true }} | ${false}
    ${{ stop_serving_flags: true }}    | ${true}
  `('reports a restriction from $values', ({ flagsPaused, values }) => {
    expect(bannerStateOf(organisation(values), undefined)).toEqual({
      flagsPaused,
      kind: 'restricted',
      over: undefined,
    })
  })

  it.each`
    values                                                                        | overBy    | kind
    ${{ overage_billing_eligible: true }}                                         | ${50000}  | ${'overage-covered'}
    ${{ overage_billing_eligible: true }}                                         | ${99999}  | ${'overage-covered'}
    ${{ overage_billing_eligible: true }}                                         | ${100000} | ${'overage-charged'}
    ${{ api_limit_grace_period_used: true, overage_billing_eligible: true }}      | ${50000}  | ${'overage-charged'}
    ${{ api_limit_restriction_enabled: true }}                                    | ${50000}  | ${'restriction-after-grace'}
    ${{ api_limit_grace_period_used: true, api_limit_restriction_enabled: true }} | ${50000}  | ${'restriction-imminent'}
    ${{}}                                                                         | ${50000}  | ${'over-limit'}
  `('is $kind for $values at $overBy over', ({ kind, overBy, values }) => {
    expect(bannerStateOf(organisation(values), { ...over, overBy })?.kind).toBe(
      kind,
    )
  })
})
