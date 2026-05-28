import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import GettingStartedPage from 'web/components/pages/GettingStartedPage'
import OnboardingQuickstartPage from 'web/components/pages/onboarding-quickstart/OnboardingQuickstartPage'

// TEMP: forced on for local validation. Revert to `Utils.getFlagsmithHasFeature(...)`
// before merge so the flag actually gates the flow.
const FORCE_ON = true

const GettingStartedSwitch: FC = () => {
  const ahaEnabled =
    FORCE_ON || Utils.getFlagsmithHasFeature('onboarding_quickstart_flow')
  return ahaEnabled ? <OnboardingQuickstartPage /> : <GettingStartedPage />
}

export default GettingStartedSwitch
