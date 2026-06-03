import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import GettingStartedPage from 'web/components/pages/GettingStartedPage'
import OnboardingQuickstartPage from 'web/components/pages/onboarding-quickstart/OnboardingQuickstartPage'
import OnboardingSinglePageContainer from 'web/components/pages/onboarding-quickstart/OnboardingSinglePageContainer'

/**
 * Routes the /getting-started surface to an onboarding variant.
 *
 * Primary gate is the multivariate flag `onboarding_experience`
 * (`control` / `stepped` / `single_page`) so the approaches can be A/B'd and
 * audiences targeted per variant — see EXPERIMENT_PLAN.md. The legacy boolean
 * `onboarding_quickstart_flow` is honoured as a fallback while the multivariate
 * flag is rolled out. Missing/`control` → the existing GettingStartedPage.
 */
const GettingStartedSwitch: FC = () => {
  const variant = Utils.getFlagsmithValue('onboarding_experience')

  if (variant === 'single_page') {
    return <OnboardingSinglePageContainer />
  }
  if (variant === 'stepped') {
    return <OnboardingQuickstartPage />
  }

  // Fallback to the legacy boolean flag until the multivariate flag exists.
  return Utils.getFlagsmithHasFeature('onboarding_quickstart_flow') ? (
    <OnboardingQuickstartPage />
  ) : (
    <GettingStartedPage />
  )
}

export default GettingStartedSwitch
