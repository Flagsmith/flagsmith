import { Organisation } from 'common/types/responses'
import { OverLimit } from './overLimit'
import { overageStatusOf } from './utils'

/** Which banner the usage page shows. One kind, one message. */
export type BannerState =
  | {
      kind: 'restricted'
      /** Absent while restricted but back under the limit. */
      over: OverLimit | undefined
      flagsPaused: boolean
    }
  | { kind: 'overage-covered'; over: OverLimit }
  | { kind: 'overage-charged'; over: OverLimit }
  | { kind: 'restriction-after-grace'; over: OverLimit }
  // The restriction task skips the 7 day wait once a grace row exists.
  | { kind: 'restriction-imminent'; over: OverLimit }
  | { kind: 'over-limit'; over: OverLimit }

export type BannerKind = BannerState['kind']

type BannerOrganisation = Pick<
  Organisation,
  | 'api_limit_grace_period_used'
  | 'api_limit_restriction_enabled'
  | 'block_access_to_admin'
  | 'overage_billing_eligible'
  | 'stop_serving_flags'
>

// Overage billing is paid only and restriction is free only, so at most one
// of them applies to an organisation.
export const bannerStateOf = (
  organisation: BannerOrganisation | undefined,
  over: OverLimit | undefined,
): BannerState | undefined => {
  // The block outlives going over the limit, so this cannot key off over.
  if (organisation?.block_access_to_admin || organisation?.stop_serving_flags) {
    return {
      flagsPaused: organisation.stop_serving_flags,
      kind: 'restricted',
      over,
    }
  }

  if (!over) {
    return undefined
  }

  const overage = overageStatusOf(
    organisation,
    over.limit + over.overBy,
    over.limit,
  )
  if (overage === 'covered') return { kind: 'overage-covered', over }
  if (overage === 'charged') return { kind: 'overage-charged', over }

  if (organisation?.api_limit_restriction_enabled) {
    return organisation.api_limit_grace_period_used
      ? { kind: 'restriction-imminent', over }
      : { kind: 'restriction-after-grace', over }
  }

  return { kind: 'over-limit', over }
}
