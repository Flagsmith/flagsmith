import React, { FC } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import { getStoredOnboardingVariant } from 'common/utils/onboardingEntry'
import GettingStartedPage from 'components/pages/GettingStartedPage'
import OnboardingFlow from './OnboardingFlow'

const GettingStartedGate: FC = () => {
  // The entry decision made at routing time (Flagsmith-on-Flagsmith,
  // anonymous identity) decides the flow; users without one get the
  // legacy page.
  const variant = getStoredOnboardingVariant()

  return variant === 'single_page' ? <OnboardingFlow /> : <GettingStartedPage />
}

export default ConfigProvider(GettingStartedGate)
