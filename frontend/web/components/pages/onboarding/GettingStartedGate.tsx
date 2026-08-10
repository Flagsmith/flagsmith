import React, { FC, useEffect } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import { getStoredOnboardingVariant } from 'common/utils/onboardingEntry'
import API from 'project/api'
import GettingStartedPage from 'components/pages/GettingStartedPage'
import OnboardingFlow from './OnboardingFlow'

const GettingStartedGate: FC = () => {
  // The entry decision made at routing time (Flagsmith-on-Flagsmith,
  // anonymous identity) decides the flow; users without one get the
  // legacy page.
  const storedVariant = getStoredOnboardingVariant()
  const variant = storedVariant ?? 'control'

  useEffect(() => {
    if (!storedVariant) return
    API.trackTraits({ onboarding_variant: storedVariant })
  }, [storedVariant])

  return variant === 'single_page' ? <OnboardingFlow /> : <GettingStartedPage />
}

export default ConfigProvider(GettingStartedGate)
