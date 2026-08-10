import flagsmith from '@flagsmith/flagsmith'
import { OnboardingVariant } from 'common/types/responses'
import { storageGet, storageRemove, storageSet } from 'common/safeLocalStorage'

const TARGETING_KEY_STORAGE_KEY = 'onboarding_targeting_key'
const VARIANT_STORAGE_KEY = 'onboarding_variant'

/**
 * Decide which onboarding flow a new user enters, before their organisation
 * exists. Identifies with an empty identifier so the API assigns a
 * pseudorandom one, reads the flag under it (recording the exposure), and
 * stores identifier and variant: the identifier becomes the organisation's
 * `targeting_key` at creation, pinning its bucketing to this decision.
 */
export async function decideOnboardingEntry(): Promise<OnboardingVariant> {
  // @ts-expect-error transient is missing from the SDK's identify type
  await flagsmith.identify('', {}, true)
  const flag = flagsmith.getExperimentFlag('onboarding_quickstart_flow')
  const identifier = flagsmith.getContext().identity?.identifier
  const variant: OnboardingVariant =
    flag?.enabled && flag.variant !== 'control' ? 'single_page' : 'control'
  if (identifier) {
    storageSet(TARGETING_KEY_STORAGE_KEY, String(identifier))
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
