import React, { FC, useEffect, useMemo, useRef, useState } from 'react'
import { useHistory } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import { useGetProfileQuery } from 'common/services/useProfile'
import { organisationService } from 'common/services/useOrganisation'
import { useCreateProjectMutation } from 'common/services/useProject'
import { useCreateEnvironmentMutation } from 'common/services/useEnvironment'
import { useCreateProjectFlagMutation } from 'common/services/useProjectFlag'
import useSelectedOrganisation from 'common/hooks/useSelectedOrganisation'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import { Req } from 'common/types/requests'
import { ProjectFlag } from 'common/types/responses'
import OnboardingStepper, {
  OnboardingStepDef,
  OnboardingStepKey,
} from 'web/components/pages/onboarding-quickstart/components/OnboardingStepper'
import InviteUsersModal from 'components/modals/InviteUsers'
import RoleStep from 'web/components/pages/onboarding-quickstart/components/RoleStep'
import OrgStep from 'web/components/pages/onboarding-quickstart/components/OrgStep'
import ProjectStep from 'web/components/pages/onboarding-quickstart/components/ProjectStep'
import FeatureStep, {
  PRESET_CUSTOM,
} from 'web/components/pages/onboarding-quickstart/components/FeatureStep'
import FeatureEvaluationStep from 'web/components/pages/onboarding-quickstart/components/FeatureEvaluationStep'
import { FEATURE_PRESETS } from 'web/components/pages/onboarding-quickstart/data/presets'
import { OnboardingRoleKey } from 'web/components/pages/onboarding-quickstart/data/roles'
import { useSmartDefaults } from 'web/components/pages/onboarding-quickstart/hooks/useSmartDefaults'
import 'web/components/pages/onboarding-quickstart/OnboardingQuickstartPage.scss'

/**
 * Telemetry placeholder — replace with the real structured-logging
 * pipeline once the feature is wired to a tracked event sink.
 */
const trackEvent = (event: string, attributes: Record<string, unknown> = {}) =>
  // eslint-disable-next-line no-console
  console.info(`[onboarding.quickstart] ${event}`, attributes)

/**
 * Create an organisation through the legacy account store rather than the RTK
 * mutation. Much of the shell still reads the current organisation from
 * `AccountStore`, and only this path populates it (adds to
 * `AccountStore.model.organisations` and sets the selection). A pure-RTK create
 * leaves `AccountStore.getOrganisation()` empty, which breaks org-scoped calls
 * on the destination page. Resolves with the new organisation id. Mirrors the
 * save/select handling in CreateOrganisationPage.
 */
const createOrganisationViaAccountStore = (name: string): Promise<number> =>
  new Promise((resolve, reject) => {
    const cleanup = () => {
      AccountStore.off('saved', onSaved)
      AccountStore.off('problem', onProblem)
      clearTimeout(timer)
    }
    const onSaved = () => {
      cleanup()
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore — savedId is set by the createOrganisation controller
      resolve(AccountStore.savedId as number)
    }
    const onProblem = () => {
      cleanup()
      reject(AccountStore.error || new Error('Failed to create organisation'))
    }
    const timer = setTimeout(() => {
      cleanup()
      reject(new Error('Timed out creating organisation'))
    }, 20000)
    AccountStore.on('saved', onSaved)
    AccountStore.on('problem', onProblem)
    AppActions.createOrganisation(name)
  })

const OnboardingQuickstartPage: FC = () => {
  const history = useHistory()
  const dispatch = useDispatch()
  const { data: profile } = useGetProfileQuery({})
  const defaults = useSmartDefaults(
    profile?.email ?? '',
    profile?.first_name ?? '',
  )

  // Self-serve signup creates and selects an organisation at registration, so
  // most users reaching onboarding already have one — reuse it and skip the
  // org step. Only when none exists do we create one (rare).
  const selectedOrganisation = useSelectedOrganisation()
  const hasExistingOrg = !!selectedOrganisation

  const [createProject] = useCreateProjectMutation()
  const [createEnvironment] = useCreateEnvironmentMutation()
  const [createProjectFlag] = useCreateProjectFlagMutation()

  const [step, setStep] = useState<OnboardingStepKey>('role')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<unknown>(null)
  const [selectedRole, setSelectedRole] = useState<OnboardingRoleKey | null>(
    null,
  )
  const [orgName, setOrgName] = useState('')
  const [projectName, setProjectName] = useState('')
  const [selectedPreset, setSelectedPreset] = useState<string>(
    FEATURE_PRESETS[0]?.key ?? '',
  )
  const [customFeature, setCustomFeature] = useState('')
  // Set from the created project + its Development environment, used to build
  // the post-onboarding features URL and the evaluation step's snippet.
  const [projectId, setProjectId] = useState<number | null>(null)
  const [environmentKey, setEnvironmentKey] = useState('')

  // Tracks entities already created so a retry after a partial failure (e.g.
  // project created but an environment call failed) reuses them rather than
  // creating duplicates. A deliberate Back + rename after a step succeeded
  // reuses the original — acceptable, since retries follow failures.
  const createdRef = useRef<{
    orgId?: number
    projectId?: number
    devKey?: string
    prodDone?: boolean
    featureDone?: boolean
  }>({})

  // Org name is pre-filled from the email domain — it's meaningful data the
  // user can keep or edit. The project name is NOT pre-filled: 'My first
  // project' is shown as placeholder text only (see ProjectStep), so the user
  // doesn't have to clear a generic default before typing their own. When left
  // blank we fall back to the placeholder via `effectiveProjectName`.
  useEffect(() => {
    setOrgName((existing) => existing || defaults.orgName)
  }, [defaults.orgName])

  const effectiveProjectName = projectName.trim() || defaults.projectName

  // Focus management — when the step changes, land focus on the first
  // interactive element of the new step. Without this, focus stays on
  // the now-invisible Next button and keyboard users have to Tab from
  // the document body to find the next field/option.
  const layoutRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const focusable = layoutRef.current?.querySelector<HTMLElement>(
      'input:not([disabled]), button:not([disabled]):not([tabindex="-1"])',
    )
    focusable?.focus()
  }, [step])

  const featureName =
    selectedPreset === PRESET_CUSTOM ? customFeature : selectedPreset

  // Final-step label varies by role — the engineer path culminates in
  // "see the SDK work", the PM path in connecting tools. Other never
  // reaches this step.
  const evaluationStepTitle =
    selectedRole === 'pm' ? 'Connect your tools' : 'See it works'

  // The timeline adapts to the user: the org step is dropped when they
  // already have one, and the evaluation step is dropped for the 'other'
  // role (Other = "orient, don't commit"), so the stepper reflects the flow
  // they'll actually walk.
  const steps: OnboardingStepDef[] = useMemo(() => {
    const base: OnboardingStepDef[] = [{ key: 'role', title: 'Your role' }]
    if (!hasExistingOrg) base.push({ key: 'org', title: 'Organisation' })
    base.push(
      { key: 'project', title: 'Project' },
      { key: 'feature', title: 'First feature' },
    )
    if (selectedRole === 'other') return base
    return [...base, { key: 'evaluation', title: evaluationStepTitle }]
  }, [evaluationStepTitle, hasExistingOrg, selectedRole])

  // Step navigation is driven by the `steps` array so it stays correct as
  // steps are added/removed (org skip, role branching) — no hardcoded
  // next/previous keys to keep in sync.
  const goToAdjacentStep = (offset: number) => {
    const index = steps.findIndex((s) => s.key === step)
    const target = steps[index + offset]
    if (target) setStep(target.key)
  }
  const goNext = () => goToAdjacentStep(1)
  const goBack = () => goToAdjacentStep(-1)

  // Post-onboarding destination. The features route expects the numeric
  // project id and the environment's api_key (not names).
  const featuresUrl = (pid: number | null, envKey: string) =>
    pid && envKey
      ? `/project/${pid}/environment/${envKey}/features`
      : '/organisations'

  const finishedDestination = featuresUrl(projectId, environmentKey)

  const handleFinish = async () => {
    setIsSubmitting(true)
    setSubmitError(null)
    trackEvent('question_step.submitted', {
      featureName,
      orgName,
      projectName: effectiveProjectName,
      role: selectedRole,
    })

    const created = createdRef.current
    try {
      // 1. Organisation — reuse the selected one, otherwise create + select.
      let organisationId = selectedOrganisation?.id ?? created.orgId
      if (!organisationId) {
        organisationId = await createOrganisationViaAccountStore(orgName)
        // Select it (sets the cookie, the Redux slice and AccountStore's
        // current org) and refresh the RTK organisation list.
        AppActions.selectOrganisation(organisationId)
        dispatch(
          organisationService.util.invalidateTags([
            { id: 'LIST', type: 'Organisation' },
          ]),
        )
        created.orgId = organisationId
      }

      // 2. Project.
      let newProjectId = created.projectId
      if (!newProjectId) {
        const project = await createProject({
          name: effectiveProjectName,
          organisation: organisationId,
        }).unwrap()
        newProjectId = project.id
        created.projectId = project.id
      }

      // 3. Environments — Development (where we land) then Production, matching
      // what normal project creation produces.
      let devKey = created.devKey
      if (!devKey) {
        const devEnvironment = await createEnvironment({
          name: 'Development',
          project: newProjectId,
        }).unwrap()
        devKey = devEnvironment.api_key
        created.devKey = devKey
      }
      if (!created.prodDone) {
        await createEnvironment({
          name: 'Production',
          project: newProjectId,
        }).unwrap()
        created.prodDone = true
      }

      // 4. First feature flag. The create endpoint only needs a small subset
      // of ProjectFlag; the request type models the full entity, so assert it.
      if (!created.featureDone) {
        const featureBody: Partial<ProjectFlag> = {
          name: featureName,
          project: newProjectId,
          type: 'STANDARD',
        }
        await createProjectFlag({
          body: featureBody as Req['createProjectFlag']['body'],
          project_id: newProjectId,
        }).unwrap()
        created.featureDone = true
      }

      // 5. Refresh the legacy organisation store so the shell (project list,
      // switcher) picks up the freshly created project without a reload.
      AppActions.refreshOrganisation()

      setProjectId(newProjectId)
      setEnvironmentKey(devKey)
      trackEvent('setup.completed', {
        projectId: newProjectId,
        role: selectedRole,
      })

      // 'other' role skips the AHA step entirely and lands on the features
      // page. Build the URL inline because the freshly-set state isn't visible
      // in this closure yet.
      if (selectedRole === 'other') {
        history.push(featuresUrl(newProjectId, devKey))
        return
      }
      setStep('evaluation')
    } catch (error) {
      trackEvent('setup.failed', { role: selectedRole })
      setSubmitError(error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSkip = () => {
    trackEvent('skipped', { atStep: step })
    history.push('/organisations')
  }

  const handleInvite = () => {
    trackEvent('invite_teammate.clicked', { role: selectedRole })
    openModal('Invite Users', <InviteUsersModal />, 'p-0 side-modal')
  }

  const handleExplore = () => {
    trackEvent('explore_dashboard.clicked', { role: selectedRole })
    history.push(finishedDestination)
  }

  const handleFirstEvalReceived = () => {
    trackEvent('first_eval.received')
  }

  return (
    <div className='onboarding-quickstart'>
      <div className='onboarding-quickstart__page'>
        <header className='onboarding-quickstart__heading'>
          <div className='onboarding-quickstart__heading-crumb text-muted'>
            Onboarding / Get your first flag working
          </div>
          <div className='onboarding-quickstart__heading-row d-flex align-items-center justify-content-between gap-3'>
            <h1 className='onboarding-quickstart__heading-title mb-0'>
              Let’s set you up in 2 minutes
            </h1>
            <Button theme='outline' size='small' onClick={handleSkip}>
              Skip — set up manually
            </Button>
          </div>
        </header>

        <OnboardingStepper
          currentStep={step}
          onStepClick={(key) => setStep(key)}
          steps={steps}
        />

        <div className='onboarding-quickstart__layout'>
          <div
            ref={layoutRef}
            className={`onboarding-quickstart__layout-content${
              step === 'evaluation'
                ? ' onboarding-quickstart__layout-content--wide'
                : ''
            }`}
          >
            {step === 'role' && (
              <RoleStep
                value={selectedRole}
                onChange={(role) => {
                  setSelectedRole(role)
                  trackEvent('role.selected', { role })
                }}
                onNext={goNext}
              />
            )}

            {step === 'org' && (
              <OrgStep value={orgName} onChange={setOrgName} onNext={goNext} />
            )}

            {step === 'project' && (
              <ProjectStep
                value={projectName}
                placeholder={defaults.projectName}
                onChange={setProjectName}
                onBack={goBack}
                onNext={goNext}
              />
            )}

            {step === 'feature' && (
              <>
                <FeatureStep
                  selectedPreset={selectedPreset}
                  customValue={customFeature}
                  isSubmitting={isSubmitting}
                  onPresetChange={setSelectedPreset}
                  onCustomChange={setCustomFeature}
                  onBack={goBack}
                  onFinish={handleFinish}
                />
                {!!submitError && (
                  <div className='mt-3'>
                    <ErrorMessage error={submitError} />
                  </div>
                )}
              </>
            )}

            {step === 'evaluation' &&
              selectedRole &&
              selectedRole !== 'other' && (
                <FeatureEvaluationStep
                  role={selectedRole}
                  environmentKey={environmentKey}
                  featureName={featureName}
                  projectName={effectiveProjectName}
                  onExplore={handleExplore}
                  onFirstEvalReceived={handleFirstEvalReceived}
                  onInvite={handleInvite}
                />
              )}
          </div>
        </div>
      </div>
    </div>
  )
}

OnboardingQuickstartPage.displayName = 'OnboardingQuickstartPage'

export default OnboardingQuickstartPage
