import React, { FC, Suspense, lazy, useState } from 'react'
import { useHistory } from 'react-router-dom'
import ErrorMessage from 'components/ErrorMessage'
import OnboardingSinglePage from 'web/components/pages/onboarding-quickstart/OnboardingSinglePage'
import { useEnsureOnboardingResources } from 'web/components/pages/onboarding-quickstart/hooks/useEnsureOnboardingResources'
import { useOnboardingFlagToggle } from 'web/components/pages/onboarding-quickstart/hooks/useOnboardingFlagToggle'
import { useUpdateOrganisationMutation } from 'common/services/useOrganisation'
import { useUpdateProjectMutation } from 'common/services/useProject'
import 'web/components/pages/onboarding-quickstart/OnboardingSinglePage.scss'

// Lazy so lottie-web + the animation JSON only load when the loading screen
// renders; the text-only fallback shows instantly meanwhile.
const OnboardingLoading = lazy(
  () => import('web/components/pages/onboarding-quickstart/OnboardingLoading'),
)

// Provides the single-page flow with real, pre-created resources (org,
// project, Dev/Prod environments, first flag) and the destination handler.
const OnboardingSinglePageContainer: FC = () => {
  const history = useHistory()
  const resources = useEnsureOnboardingResources()
  const [updateOrganisation] = useUpdateOrganisationMutation()
  const [updateProject] = useUpdateProjectMutation()
  // The flag name is editable and drives the snippets, console and toggle, so
  // it lives in state here (optimistic) rather than reading the constant each
  // render. The rename also persists server-side (see renameFeature).
  const [featureName, setFeatureName] = useState(resources.featureName)
  const flagToggle = useOnboardingFlagToggle({
    environment: resources.environment,
    featureName,
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
  // Renaming the flag must persist (the snippet name and the real flag have to
  // stay in lockstep, or the user's code reads a flag that doesn't exist).
  // Optimistic: show the new name immediately, revert if the delete+recreate
  // fails (e.g. the name breaks the project's feature-name regex). The page
  // sends an already-sanitised name.
  const renameFeature = async (name: string) => {
    const previous = featureName
    setFeatureName(name)
    const ok = await flagToggle.rename(name)
    if (!ok) {
      setFeatureName(previous)
      toast('Couldn’t rename your flag. Please try again.')
    }
  }

  const goToDashboard = () => {
    history.push(
      resources.projectId && resources.environmentKey
        ? `/project/${resources.projectId}/environment/${resources.environmentKey}/features`
        : '/organisations',
    )
  }

  // TEMP (preview only): the real "first request received" signal doesn't exist
  // yet, so the connected state can't fire for real. `?connected=1` lets us
  // preview the v3 connected design (green console, unlocked flag/quests).
  // Remove once the real first-traffic signal is wired in.
  const connectedPreview =
    new URLSearchParams(window.location.search).get('connected') === '1'

  if (resources.status === 'creating') {
    return (
      <Suspense
        fallback={
          <div className='onboarding-single'>
            <div className='onboarding-single__page onboarding-single__loading text-muted'>
              Setting up your workspace…
            </div>
          </div>
        }
      >
        <OnboardingLoading />
      </Suspense>
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
      featureName={featureName}
      caseSensitive={resources.caseSensitive}
      environmentKey={resources.environmentKey}
      connected={connectedPreview}
      flagEnabled={flagToggle.enabled}
      flagToggleDisabled={!flagToggle.isReady || flagToggle.isLoading}
      onToggleFlag={flagToggle.toggle}
      onRenameOrganisation={renameOrganisation}
      onRenameProject={renameProject}
      onRenameFeature={renameFeature}
      onGoToDashboard={goToDashboard}
    />
  )
}

export default OnboardingSinglePageContainer
