import Utils from './utils'

export type OnboardingVariant = 'control' | 'single_page'

// The served variant name picks the arm ('control' is the reserved key the
// API reports for the default arm). Enabled with no variant is the
// pre-conversion boolean flag, which means the new flow.
export const isSinglePageOnboarding = (): boolean =>
  Utils.getFlagsmithHasFeature('onboarding_quickstart_flow') &&
  Utils.getFlagsmithVariant('onboarding_quickstart_flow') !== 'control'

export const getOnboardingVariant = (): OnboardingVariant =>
  isSinglePageOnboarding() ? 'single_page' : 'control'
