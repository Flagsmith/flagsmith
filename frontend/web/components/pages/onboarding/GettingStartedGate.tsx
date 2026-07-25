import React, { FC, useEffect } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import ConfigProvider from 'common/providers/ConfigProvider'
import {
  getOnboardingVariant,
  isSinglePageOnboarding,
} from 'common/utils/getOnboardingVariant'
import API from 'project/api'
import GettingStartedPage from 'components/pages/GettingStartedPage'
import OnboardingFlow from './OnboardingFlow'

const GettingStartedGate: FC = () => {
  // ConfigProvider re-renders the gate on every SDK fetch; only tag the
  // variant once the server has answered for this identity.
  const trustworthy =
    !flagsmith.loadingState?.isFetching &&
    flagsmith.loadingState?.source === 'SERVER' &&
    !!flagsmith.getContext().identity

  const variant = getOnboardingVariant()

  useEffect(() => {
    if (!trustworthy) return
    API.trackTraits({ onboarding_variant: variant })
  }, [trustworthy, variant])

  return isSinglePageOnboarding() ? <OnboardingFlow /> : <GettingStartedPage />
}

export default ConfigProvider(GettingStartedGate)
