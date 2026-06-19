import React, { FC, useState } from 'react'
import { useHistory } from 'react-router-dom'
import Button from 'components/base/forms/Button'
import OnboardingHeader from 'components/pages/onboarding/OnboardingHeader'
import ThemeToggle from 'components/pages/onboarding/ThemeToggle'
import OnboardingConnectPanel from 'components/pages/onboarding/OnboardingConnectPanel'
import { useEnsureOnboardingResources } from 'components/pages/onboarding/hooks/useEnsureOnboardingResources'
import { useOnboardingFlagRename } from 'components/pages/onboarding/hooks/useOnboardingFlagRename'
import { useUpdateOrganisationMutation } from 'common/services/useOrganisation'
import { useUpdateProjectMutation } from 'common/services/useProject'
import './OnboardingFlow.scss'

// The new single-page onboarding experience, rendered at /getting-started when
// the `onboarding_quickstart_flow` flag is on (see GettingStartedGate).
//
// Resources (org / project / Dev + Prod / first flag) are bootstrapped
// idempotently by useEnsureOnboardingResources, and the inline header chips
// persist renames. TODO(#7766): the verify console / flags table land on top.
const OnboardingFlow: FC = () => {
  const {
    caseSensitive,
    environment,
    environmentKey,
    featureName: bootstrappedFeatureName,
    organisationId,
    organisationName,
    projectId,
    projectName,
    status,
  } = useEnsureOnboardingResources()

  const history = useHistory()
  const [updateOrganisation] = useUpdateOrganisationMutation()
  const [updateProject] = useUpdateProjectMutation()

  // The flow is chromeless (no app nav), so it owns its only way out: skip to
  // the org's projects and set things up manually.
  const skipToApp = () =>
    history.push(
      organisationId !== null
        ? `/organisation/${organisationId}/projects`
        : '/',
    )
  // The flag name drives the connect-panel snippets/prompt, so it's optimistic
  // state here: shown immediately on rename, reverted if the persist fails.
  const [featureName, setFeatureName] = useState(bootstrappedFeatureName)
  const { isReady: flagReady, rename: renameFlag } = useOnboardingFlagRename({
    environment,
    featureName,
    projectId,
  })

  // Persist inline renames. Org/project are single-field PATCHes; the chip owns
  // the optimistic display (the shell nav adopts the new names on its next load).
  const renameOrganisation = (name: string) => {
    if (organisationId !== null) {
      updateOrganisation({ body: { name }, id: organisationId })
    }
  }
  const renameProject = (name: string) => {
    if (projectId !== null) {
      updateProject({ body: { name }, id: projectId })
    }
  }
  // The flag and its snippet name must stay in lockstep, so this persists
  // (delete + recreate). Optimistic, reverting on failure.
  const renameFeature = async (name: string) => {
    const previous = featureName
    setFeatureName(name)
    if (!(await renameFlag(name))) {
      setFeatureName(previous)
      // Only surface an error for a genuine failure — a rename attempted before
      // the flag query settles also returns false, and shouldn't alarm the user.
      if (flagReady) {
        toast('Couldn’t rename your flag. Please try again.', 'danger')
      }
    }
  }

  if (status === 'creating') {
    return (
      <div className='onboarding-flow mx-auto text-center'>
        <Loader />
      </div>
    )
  }

  // Bootstrap failed (e.g. a plan org cap, or a network error). Without this the
  // flow would render with an empty environment key and broken snippets, so show
  // a recoverable message instead. A reload re-runs the idempotent bootstrap.
  if (status === 'error') {
    return (
      <div className='onboarding-flow mx-auto text-center'>
        <h2 className='mb-2'>We couldn’t set up your workspace</h2>
        <p className='text-muted mb-3'>
          Something went wrong creating your starter project. Please try again.
        </p>
        <Button onClick={() => window.location.reload()}>Try again</Button>
      </div>
    )
  }

  return (
    <div className='onboarding-flow mx-auto d-flex flex-column gap-4'>
      <div className='d-flex justify-content-end'>
        <ThemeToggle />
      </div>
      <OnboardingHeader
        organisationName={organisationName}
        projectName={projectName}
        featureName={featureName}
        caseSensitive={caseSensitive}
        onRenameOrganisation={renameOrganisation}
        onRenameProject={renameProject}
        onRenameFeature={renameFeature}
      />
      <OnboardingConnectPanel
        environmentKey={environmentKey}
        featureName={featureName}
      />
      <div className='d-flex justify-content-end'>
        <Button theme='text' onClick={skipToApp}>
          Skip — set up manually
        </Button>
      </div>
    </div>
  )
}

export default OnboardingFlow
