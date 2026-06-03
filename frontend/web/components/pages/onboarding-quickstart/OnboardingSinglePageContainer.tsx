import React, { FC } from 'react'
import { useHistory } from 'react-router-dom'
import ErrorMessage from 'components/ErrorMessage'
import OnboardingSinglePage from 'web/components/pages/onboarding-quickstart/OnboardingSinglePage'
import { useEnsureOnboardingResources } from 'web/components/pages/onboarding-quickstart/hooks/useEnsureOnboardingResources'
import 'web/components/pages/onboarding-quickstart/OnboardingSinglePage.scss'

// Provides the single-page flow with real, pre-created resources (org,
// project, Dev/Prod environments, first flag) and the destination handler.
const OnboardingSinglePageContainer: FC = () => {
  const history = useHistory()
  const resources = useEnsureOnboardingResources()

  const goToDashboard = () => {
    history.push(
      resources.projectId && resources.environmentKey
        ? `/project/${resources.projectId}/environment/${resources.environmentKey}/features`
        : '/organisations',
    )
  }

  if (resources.status === 'creating') {
    return (
      <div className='onboarding-single'>
        <div className='onboarding-single__page onboarding-single__loading text-muted'>
          Setting up your workspace…
        </div>
      </div>
    )
  }

  if (resources.status === 'error') {
    return (
      <div className='onboarding-single'>
        <div className='onboarding-single__page'>
          <ErrorMessage error={resources.error} />
        </div>
      </div>
    )
  }

  return (
    <OnboardingSinglePage
      organisationName={resources.organisationName}
      projectName={resources.projectName}
      featureName={resources.featureName}
      environmentKey={resources.environmentKey}
      onGoToDashboard={goToDashboard}
    />
  )
}

export default OnboardingSinglePageContainer
