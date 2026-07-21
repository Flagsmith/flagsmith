import Utils from './utils'

export type OnboardingVariant = 'control' | 'single_page'

export const getOnboardingVariant = (): OnboardingVariant =>
  Utils.getFlagsmithHasFeature('onboarding_quickstart_flow')
    ? 'single_page'
    : 'control'

export const isSinglePageOnboarding = (): boolean =>
  getOnboardingVariant() === 'single_page'
