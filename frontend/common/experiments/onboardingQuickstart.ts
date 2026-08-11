import { useEffect } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import { OnboardingVariant } from 'common/types/responses'
import { storageGet, storageRemove, storageSet } from 'common/safeLocalStorage'
import API from 'project/api'

/**
 * The onboarding quickstart experiment: new users are served either the
 * legacy getting-started page (`control`) or the single-page onboarding
 * flow (`single_page`), split on organisations via the
 * `onboarding_quickstart_flow` Flagsmith-on-Flagsmith flag.
 *
 * Everything the experiment touches on the frontend imports from this
 * module. When the experiment concludes, delete this module and unpick
 * its importers.
 */

const TARGETING_KEY_STORAGE_KEY = 'onboarding_targeting_key'
const VARIANT_STORAGE_KEY = 'onboarding_variant'

export type OnboardingEntryDecision = {
  variant: OnboardingVariant
  targetingKey: string | null
}

/**
 * Decide which onboarding flow a new user enters, before their organisation
 * exists. Identifies with an empty identifier so the API assigns a
 * pseudorandom one and reads the flag under it (recording the exposure).
 *
 * Persists nothing: the caller races this against a timeout, and a late
 * decision must not be stored — by then the SDK identity may already be
 * the logged-in user, and the routing it should have driven has happened.
 * Call `persistOnboardingEntry` with an accepted decision.
 */
export async function decideOnboardingEntry(): Promise<OnboardingEntryDecision> {
  // @ts-expect-error transient is missing from the SDK's identify type
  await flagsmith.identify('', {}, true)
  const flag = flagsmith.getExperimentFlag('onboarding_quickstart_flow')
  const identifier = flagsmith.getContext().identity?.identifier
  const variant: OnboardingVariant =
    flag?.enabled && flag.variant !== 'control' ? 'single_page' : 'control'
  return { targetingKey: identifier ? String(identifier) : null, variant }
}

/**
 * Store an accepted entry decision. The identifier becomes the
 * organisation's `targeting_key` at creation, pinning its bucketing to
 * this decision. Returns the effective variant: a non-control variant
 * without an assigned identifier cannot be pinned, so it downgrades to
 * `control`.
 */
export function persistOnboardingEntry(
  decision: OnboardingEntryDecision,
): OnboardingVariant {
  const variant =
    decision.variant !== 'control' && !decision.targetingKey
      ? 'control'
      : decision.variant
  if (decision.targetingKey) {
    storageSet(TARGETING_KEY_STORAGE_KEY, decision.targetingKey)
  }
  storageSet(VARIANT_STORAGE_KEY, variant)
  return variant
}

export const getStoredOnboardingVariant = (): OnboardingVariant | null => {
  const variant = storageGet(VARIANT_STORAGE_KEY)
  return variant === 'single_page' || variant === 'control' ? variant : null
}

export const getStoredOnboardingTargetingKey = (): string | null =>
  storageGet(TARGETING_KEY_STORAGE_KEY)

// Called once the user holds membership of any organisation; a later
// organisation must not consume the key, or two organisations would
// share one experiment subject.
export const clearOnboardingTargetingKey = (): void =>
  storageRemove(TARGETING_KEY_STORAGE_KEY)

/**
 * The stored entry decision, with the variant tagged onto the user's
 * analytics profile as a side effect. `variant` is null for users who
 * never went through the entry decision — render them the legacy page.
 */
export function useOnboardingQuickstart(): {
  isSinglePage: boolean
  variant: OnboardingVariant | null
} {
  const variant = getStoredOnboardingVariant()

  useEffect(() => {
    if (!variant) return
    API.trackTraits({ onboarding_variant: variant })
  }, [variant])

  return { isSinglePage: variant === 'single_page', variant }
}
