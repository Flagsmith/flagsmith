import React, { FC, useState } from 'react'
import { useHistory } from 'react-router-dom'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import OnboardingHeader from 'components/pages/onboarding/OnboardingHeader'
import ThemeToggle from 'components/pages/onboarding/ThemeToggle'
import OnboardingConnectPanel from 'components/pages/onboarding/OnboardingConnectPanel'
import OnboardingTerminal from 'components/pages/onboarding/OnboardingTerminal'
import OnboardingFlagsTable from 'components/pages/onboarding/OnboardingFlagsTable'
import { useEnsureOnboardingResources } from 'components/pages/onboarding/hooks/useEnsureOnboardingResources'
import { useOnboardingFlagRename } from 'components/pages/onboarding/hooks/useOnboardingFlagRename'
import { useOnboardingFlag } from 'components/pages/onboarding/hooks/useOnboardingFlag'
import { useOnboardingConnection } from 'components/pages/onboarding/hooks/useOnboardingConnection'
import { useUpdateOrganisationMutation } from 'common/services/useOrganisation'
import { useUpdateProjectMutation } from 'common/services/useProject'
import './OnboardingFlow.scss'

// The new single-page onboarding experience, rendered at /getting-started when
// the `onboarding_quickstart_flow` flag is on (see GettingStartedGate).
//
// Resources (org / project / Dev + Prod / first flag) are bootstrapped
// idempotently by useEnsureOnboardingResources, and the inline header chips
// persist renames; the verify terminal and flags table render below (#7766).
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
  // Inline renames are optimistic and revert if the persist fails. The flag name
  // also drives the connect-panel snippets/prompt, so it defaults to the
  // bootstrapped flag (its real name, reused on revisit).
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

  // Verify terminal + flags table. The checklist ticks as the user copies the
  // install / wire snippets; the connection step is stubbed until the
  // first-evaluation signal lands (#7767, behind useOnboardingConnection); the
  // Dev toggle is real now.
  const connection = useOnboardingConnection()
  // Session-only and one-way: a reload resets them, so the checklist reflects
  // what the user did this visit, not durable progress. Fine for onboarding.
  const [installCopied, setInstallCopied] = useState(false)
  const [snippetCopied, setSnippetCopied] = useState(false)
  const {
    enabled: flagEnabled,
    isToggling,
    ready: flagStateReady,
    tags: flagTags,
    toggle: toggleFlag,
  } = useOnboardingFlag(environment, projectId, featureName)

  // Org/project are single-field PATCHes; the shell nav adopts the new names on
  // its next load.
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
  // The flag and its snippet name must stay in lockstep, so this persists
  // (delete + recreate). Optimistic, reverting on failure.
  const renameFeature = async (name: string) => {
    const previous = featureName
    setRenamedFeature(name)
    if (await renameFlag(name)) {
      toast('Flag name updated')
    } else {
      setRenamedFeature(previous)
      // Only surface an error for a genuine failure - a rename attempted before
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
