import flagsmith from '@flagsmith/flagsmith'
import { OnboardingVariant } from 'common/types/responses'
import { storageGet, storageRemove, storageSet } from 'common/safeLocalStorage'

const TARGETING_KEY_STORAGE_KEY = 'onboarding_targeting_key'
const VARIANT_STORAGE_KEY = 'onboarding_variant'

export const ONBOARDING_FLAG_NAME = 'onboarding_quickstart_flow'

export type OnboardingEntryDecision = {
  variant: OnboardingVariant
  targetingKey: string | null
}

/**
 * Decide which onboarding flow a new user enters, before their organisation
 * exists. Identifies with an empty identifier so the API assigns a
 * pseudorandom one, then reads the flag under it.
 *
 * Reads the flag without recording an exposure: the caller races this against
 * a timeout, so being asked the question is not the same as being shown the
 * answer. `trackOnboardingExposure` records it once the variant is applied.
 *
 * Persists nothing: a late decision must not be stored — by then the SDK
 * identity may already be the logged-in user, and the routing it should have
 * driven has happened. Call `persistOnboardingEntry` with an accepted decision.
 */
export async function decideOnboardingEntry(): Promise<OnboardingEntryDecision> {
  // @ts-expect-error transient is missing from the SDK's identify type
  await flagsmith.identify('', {}, true)
  const flag = flagsmith.getState().flags?.[ONBOARDING_FLAG_NAME]
  const identifier = flagsmith.getContext().identity?.identifier
  const variant: OnboardingVariant =
    flag?.enabled && flag.variant !== 'control' ? 'single_page' : 'control'
  return { targetingKey: identifier ? String(identifier) : null, variant }
}

/**
 * Record the exposure for the variant the user was actually routed to, against
 * the identifier that becomes the organisation's targeting key. Skipped when
 * there is no identifier: without one nothing was assigned, so the user was
 * never in the experiment.
 */
export function trackOnboardingExposure(
  decision: OnboardingEntryDecision,
  appliedVariant: OnboardingVariant,
): void {
  if (!decision.targetingKey) {
    return
  }
  flagsmith.trackExposureEvent(ONBOARDING_FLAG_NAME, {
    identifier: decision.targetingKey,
    value: appliedVariant,
  })
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

// Called once an organisation owns the key; a later organisation must not
// reuse it, or two organisations would share one experiment subject.
export const clearOnboardingTargetingKey = (): void =>
  storageRemove(TARGETING_KEY_STORAGE_KEY)
