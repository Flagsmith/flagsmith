import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import GettingStartedPage from 'components/pages/GettingStartedPage'
import OnboardingFlow from './OnboardingFlow'

// Gates /getting-started: renders the new onboarding flow when the
// `onboarding_quickstart_flow` flag is on, otherwise the existing page.
//
// Deliberately a flat file, not a folder + barrel - a one-line route gate with
// no styles or sub-parts, the documented exception to the component-folder
// convention (frontend/CLAUDE.md rule 8).
const GettingStartedGate: FC = () =>
  Utils.getFlagsmithHasFeature('onboarding_quickstart_flow') ? (
    <OnboardingFlow />
  ) : (
    <GettingStartedPage />
  )

export default GettingStartedGate
