import React, { FC, useState } from 'react'
import { useHistory } from 'react-router-dom'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import OnboardingHeader from 'components/pages/onboarding/OnboardingHeader'
import ThemeToggle from 'components/pages/onboarding/ThemeToggle'
import OnboardingConnectPanel from 'components/pages/onboarding/OnboardingConnectPanel'
import OnboardingTerminal from 'components/pages/onboarding/OnboardingTerminal'
import OnboardingFlagsTable from 'components/pages/onboarding/OnboardingFlagsTable'
import OnboardingNextSteps, {
  OnboardingNextStep,
} from 'components/pages/onboarding/OnboardingNextSteps'
import { useEnsureOnboardingResources } from 'components/pages/onboarding/hooks/useEnsureOnboardingResources'
import { useOnboardingFlagRename } from 'components/pages/onboarding/hooks/useOnboardingFlagRename'
import { useOnboardingFlag } from 'components/pages/onboarding/hooks/useOnboardingFlag'
import { useOnboardingConnection } from 'components/pages/onboarding/hooks/useOnboardingConnection'
import { useUpdateOrganisationMutation } from 'common/services/useOrganisation'
import { useUpdateProjectMutation } from 'common/services/useProject'
import './OnboardingFlow.scss'

// The single-page onboarding flow, rendered at /getting-started when
// onboarding_quickstart_flow is on (see GettingStartedGate).
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

  // Chromeless flow, so it owns its only exit.
  const skipToApp = () =>
    history.push(
      organisationId !== null
        ? `/organisation/${organisationId}/projects`
        : '/',
    )
  // Inline renames are optimistic, reverting on failure. featureName drives the
  // snippets, so it defaults to the bootstrapped flag.
  const [renamedOrganisation, setRenamedOrganisation] = useState<string | null>(
    null,
  )
  const [renamedProject, setRenamedProject] = useState<string | null>(null)
  const [renamedFeature, setRenamedFeature] = useState<string | null>(null)
  const organisationDisplayName = renamedOrganisation ?? organisationName
  const projectDisplayName = renamedProject ?? projectName
  const featureName = renamedFeature ?? bootstrappedFeatureName
  const { isReady: flagReady, rename: renameFlag } = useOnboardingFlagRename({
    environment,
    featureName,
    projectId,
  })

  // Connection is stubbed until #7767 (useOnboardingConnection); the toggle is real.
  const connection = useOnboardingConnection()
  // Session-only: a reload resets the checklist. Fine for onboarding.
  const [installCopied, setInstallCopied] = useState(false)
  const [snippetCopied, setSnippetCopied] = useState(false)
  const {
    enabled: flagEnabled,
    flagId,
    isToggling,
    ready: flagStateReady,
    tags: flagTags,
    toggle: toggleFlag,
  } = useOnboardingFlag(environment, projectId, featureName)

  // Single-field PATCHes; the shell adopts the new names on its next load.
  const renameOrganisation = async (name: string) => {
    if (organisationId === null) {
      return
    }
    const previous = organisationDisplayName
    setRenamedOrganisation(name)
    try {
      await updateOrganisation({ body: { name }, id: organisationId }).unwrap()
      toast('Organisation name updated')
    } catch {
      setRenamedOrganisation(previous)
      toast(
        'Couldn’t update your organisation name. Please try again.',
        'danger',
      )
    }
  }
  const renameProject = async (name: string) => {
    if (projectId === null) {
      return
    }
    const previous = projectDisplayName
    setRenamedProject(name)
    try {
      await updateProject({ body: { name }, id: projectId }).unwrap()
      toast('Project name updated')
    } catch {
      setRenamedProject(previous)
      toast('Couldn’t update your project name. Please try again.', 'danger')
    }
  }
  // Flag name and snippet stay in lockstep; persists via delete + recreate.
  const renameFeature = async (name: string) => {
    const previous = featureName
    setRenamedFeature(name)
    if (await renameFlag(name)) {
      toast('Flag name updated')
    } else {
      setRenamedFeature(previous)
      // Don't alarm on a rename fired before the flag query settles.
      if (flagReady) {
        toast('Couldn’t rename your flag. Please try again.', 'danger')
      }
    }
  }

  // Each next-step card deep-links to the flag's real config; nothing faked.
  const goToNextStep = (step: OnboardingNextStep) => {
    if (projectId === null) {
      return
    }
    const base = `/project/${projectId}/environment/${environmentKey}`
    if (step === 'experiment') {
      history.push(`${base}/experiments`)
      return
    }
    if (flagId === null) {
      return
    }
    // Tab param is the slugified tab label (see TabMenu/Tabs urlParam).
    const tab = step === 'rollout' ? 'segment-overrides' : 'value'
    history.push(`${base}/features?feature=${flagId}&tab=${tab}`)
  }

  if (status === 'creating') {
    return (
      <div className='onboarding-flow mx-auto text-center'>
        <Loader />
      </div>
    )
  }

  // Bootstrap failed (e.g. a plan org cap). Recoverable; a reload re-runs it.
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
        organisationName={organisationDisplayName}
        projectName={projectDisplayName}
        featureName={featureName}
        caseSensitive={caseSensitive}
        onRenameOrganisation={renameOrganisation}
        onRenameProject={renameProject}
        onRenameFeature={renameFeature}
      />
      <OnboardingConnectPanel
        environmentKey={environmentKey}
        featureName={featureName}
        onCopyInstall={() => setInstallCopied(true)}
        onCopyWire={() => setSnippetCopied(true)}
      />
      <OnboardingTerminal
        featureName={featureName}
        installCopied={installCopied}
        snippetCopied={snippetCopied}
        connected={connection === 'connected'}
      />
      <OnboardingFlagsTable
        status={connection === 'connected' ? 'connected' : 'waiting'}
        flags={[
          {
            description: 'Controls the demo button shown to your users',
            enabled: flagEnabled,
            name: featureName,
            tags: flagTags,
          },
        ]}
        onToggle={(_flag, next) => toggleFlag(next)}
        togglingFlag={isToggling ? featureName : null}
        togglesReady={flagStateReady}
      />
      <OnboardingNextSteps
        locked={connection !== 'connected'}
        onSelect={goToNextStep}
      />
      <div className='d-flex justify-content-end'>
        <Button theme='text' onClick={skipToApp}>
          <span className='d-inline-flex align-items-center gap-1'>
            Skip onboarding, I’m a pro
            <Icon name='arrow-right' width={14} />
          </span>
        </Button>
      </div>
    </div>
  )
}

export default OnboardingFlow
