import React, { FC } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useOnboardingQuickstart } from 'common/experiments/onboardingQuickstart'
import GettingStartedPage from 'components/pages/GettingStartedPage'
import OnboardingFlow from './OnboardingFlow'

const GettingStartedGate: FC = () => {
  const { isSinglePage } = useOnboardingQuickstart()
  return isSinglePage ? <OnboardingFlow /> : <GettingStartedPage />
}

export default ConfigProvider(GettingStartedGate)
