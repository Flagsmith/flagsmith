import React, { FC } from 'react'
import { useHistory } from 'react-router-dom'
import ErrorMessage from 'components/ErrorMessage'
import OnboardingSinglePage from 'web/components/pages/onboarding-quickstart/OnboardingSinglePage'
import { useEnsureOnboardingResources } from 'web/components/pages/onboarding-quickstart/hooks/useEnsureOnboardingResources'
import { useOnboardingFlagToggle } from 'web/components/pages/onboarding-quickstart/hooks/useOnboardingFlagToggle'
import { useUpdateOrganisationMutation } from 'common/services/useOrganisation'
import { useUpdateProjectMutation } from 'common/services/useProject'
import 'web/components/pages/onboarding-quickstart/OnboardingSinglePage.scss'

// Provides the single-page flow with real, pre-created resources (org,
// project, Dev/Prod environments, first flag) and the destination handler.
const OnboardingSinglePageContainer: FC = () => {
  const history = useHistory()
  const resources = useEnsureOnboardingResources()
  const [updateOrganisation] = useUpdateOrganisationMutation()
  const [updateProject] = useUpdateProjectMutation()
  const flagToggle = useOnboardingFlagToggle({
    environment: resources.environment,
    featureName: resources.featureName,
    projectId: resources.projectId,
  })

  // Persist inline renames. Only `name` is required by either body, so a rename
  // is a single-field patch; the page owns the optimistic display, this keeps
  // the server in sync. The shell nav adopts the new names on its next load.
  const renameOrganisation = (name: string) => {
    if (resources.organisationId !== null) {
      updateOrganisation({ body: { name }, id: resources.organisationId })
    }
  }
  const renameProject = (name: string) => {
    if (resources.projectId !== null) {
      updateProject({ body: { name }, id: resources.projectId })
    }
  }

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
      flagEnabled={flagToggle.enabled}
      flagToggleDisabled={!flagToggle.isReady || flagToggle.isLoading}
      onToggleFlag={flagToggle.toggle}
      onRenameOrganisation={renameOrganisation}
      onRenameProject={renameProject}
      onGoToDashboard={goToDashboard}
    />
  )
}

export default OnboardingSinglePageContainer
