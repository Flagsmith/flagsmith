import { Organisation } from 'common/types/responses'
import { OverLimit } from './overLimit'

export type LimitStatus =
  | {
      kind: 'restricted'
      // Undefined once back under the limit.
      over: OverLimit | undefined
      flagsPaused: boolean
      apiLimitAccessBlocked: boolean
    }
  | { kind: 'overage-covered'; over: OverLimit }
  | { kind: 'overage-charged'; over: OverLimit }
  | { kind: 'restriction-after-grace'; over: OverLimit }
  // The restriction task skips the 7 day wait once a grace row exists.
  | { kind: 'restriction-imminent'; over: OverLimit }
  | { kind: 'over-limit'; over: OverLimit }

export type LimitStatusKind = LimitStatus['kind']

export type LimitOrganisation = Pick<
  Organisation,
  | 'api_limit_access_blocked'
  | 'api_limit_grace_period_used'
  | 'api_limit_restriction_enabled'
  | 'block_access_to_admin'
  | 'overage_billing_eligible'
  | 'stop_serving_flags'
>

export const NO_LIMIT_FLAGS: LimitOrganisation = {
  api_limit_access_blocked: false,
  api_limit_grace_period_used: false,
  api_limit_restriction_enabled: false,
  block_access_to_admin: false,
  overage_billing_eligible: false,
  stop_serving_flags: false,
}

// Overage billing is paid only and restriction free only, so one applies at most.
export const limitStatusOf = (
  organisation: LimitOrganisation | undefined,
  over: OverLimit | undefined,
): LimitStatus | undefined => {
  // The block outlives going over the limit, so this cannot key off over.
  // An API-limit block is a restriction on its own: the row can remain
  // after both boolean flags have been cleared.
  if (
    organisation?.block_access_to_admin ||
    organisation?.stop_serving_flags ||
    organisation?.api_limit_access_blocked
  ) {
    return {
      apiLimitAccessBlocked: organisation.api_limit_access_blocked,
      flagsPaused: organisation.stop_serving_flags,
      kind: 'restricted',
      over,
    }
  }

  if (!over) {
    return undefined
  }

  // Mirrors charge_for_api_call_count_overages: the first overage is free
  // unless usage reaches twice the limit.
  if (organisation?.overage_billing_eligible) {
    const charged =
      organisation.api_limit_grace_period_used || over.overBy >= over.limit
    return { kind: charged ? 'overage-charged' : 'overage-covered', over }
  }

  if (organisation?.api_limit_restriction_enabled) {
    return organisation.api_limit_grace_period_used
      ? { kind: 'restriction-imminent', over }
      : { kind: 'restriction-after-grace', over }
  }

  return { kind: 'over-limit', over }
}
