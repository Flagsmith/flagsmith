import React, { FC, useEffect } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import AccountStore from 'common/stores/account-store'
import API from 'project/api'
import GettingStartedPage from 'components/pages/GettingStartedPage'
import OnboardingFlow from './OnboardingFlow'

const GettingStartedGate: FC = () => {
  // The backend decides the variant per organisation and serves it on the
  // organisation payload; the exposure is recorded server-side.
  const organisation = AccountStore.getOrganisation()
  const variant = organisation?.onboarding_variant ?? 'control'

  useEffect(() => {
    if (!organisation?.id) return
    API.trackTraits({ onboarding_variant: variant })
  }, [organisation?.id, variant])

  return variant === 'single_page' ? <OnboardingFlow /> : <GettingStartedPage />
}

export default ConfigProvider(GettingStartedGate)
