import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import GettingStartedPage from 'web/components/pages/GettingStartedPage'
import OnboardingQuickstartPage from 'web/components/pages/onboarding-quickstart/OnboardingQuickstartPage'

const GettingStartedSwitch: FC = () => {
  const quickstartEnabled = Utils.getFlagsmithHasFeature(
    'onboarding_quickstart_flow',
  )
  return quickstartEnabled ? (
    <OnboardingQuickstartPage />
  ) : (
    <GettingStartedPage />
  )
}

export default GettingStartedSwitch
