import React, { FC, useEffect } from 'react'
import {
  getOnboardingVariant,
  isSinglePageOnboarding,
} from 'common/utils/getOnboardingVariant'
import API from 'project/api'
import GettingStartedPage from 'components/pages/GettingStartedPage'
import OnboardingFlow from './OnboardingFlow'

const GettingStartedGate: FC = () => {
  const variant = getOnboardingVariant()

  useEffect(() => {
    API.trackTraits({ onboarding_variant: variant })
  }, [variant])

  return isSinglePageOnboarding() ? <OnboardingFlow /> : <GettingStartedPage />
}

export default GettingStartedGate
