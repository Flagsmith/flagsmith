import React, { FC, useEffect, useMemo, useRef, useState } from 'react'
import { useHistory } from 'react-router-dom'
import Button from 'components/base/forms/Button'
import { useGetProfileQuery } from 'common/services/useProfile'
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

const OnboardingQuickstartPage: FC = () => {
  const history = useHistory()
  const { data: profile } = useGetProfileQuery({})
  const defaults = useSmartDefaults(
    profile?.email ?? '',
    profile?.first_name ?? '',
  )

  const [step, setStep] = useState<OnboardingStepKey>('role')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [selectedRole, setSelectedRole] = useState<OnboardingRoleKey | null>(
    null,
  )
  const [orgName, setOrgName] = useState('')
  const [projectName, setProjectName] = useState('')
  const [selectedPreset, setSelectedPreset] = useState<string>(
    FEATURE_PRESETS[0]?.key ?? '',
  )
  const [customFeature, setCustomFeature] = useState('')
  const [environmentKey, setEnvironmentKey] = useState('')

  useEffect(() => {
    setOrgName((existing) => existing || defaults.orgName)
    setProjectName((existing) => existing || defaults.projectName)
  }, [defaults.orgName, defaults.projectName])

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

  const steps: OnboardingStepDef[] = useMemo(
    () => [
      { key: 'role', title: 'Your role' },
      { key: 'org', title: 'Organisation' },
      { key: 'project', title: 'Project' },
      { key: 'feature', title: 'First feature' },
      { key: 'evaluation', title: evaluationStepTitle },
    ],
    [evaluationStepTitle],
  )

  // Post-onboarding destination. Real impl needs projectId + environmentKey
  // returned from the API-chain stub in handleFinish — both are currently
  // placeholders so the URL won't fully resolve until that lands.
  const finishedDestination =
    environmentKey && projectName
      ? `/project/${projectName}/environment/${environmentKey}/features`
      : '/organisations'

  const handleFinish = async () => {
    setIsSubmitting(true)
    trackEvent('question_step.submitted', {
      featureName,
      orgName,
      projectName,
      role: selectedRole,
    })
    // POC stub — real impl would chain createOrganisation → createProject →
    // createFeature → fetch environment key here.
    setEnvironmentKey('demo-environment-key-replace-me')
    setIsSubmitting(false)

    // 'other' role skips the AHA step entirely and lands on the features
    // page — per the per-role paths design, Other = "orient, don't commit".
    if (selectedRole === 'other') {
      history.push(finishedDestination)
      return
    }
    setStep('evaluation')
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
                onNext={() => setStep('org')}
              />
            )}

            {step === 'org' && (
              <OrgStep
                value={orgName}
                onChange={setOrgName}
                onNext={() => setStep('project')}
              />
            )}

            {step === 'project' && (
              <ProjectStep
                value={projectName}
                onChange={setProjectName}
                onBack={() => setStep('org')}
                onNext={() => setStep('feature')}
              />
            )}

            {step === 'feature' && (
              <FeatureStep
                selectedPreset={selectedPreset}
                customValue={customFeature}
                isSubmitting={isSubmitting}
                onPresetChange={setSelectedPreset}
                onCustomChange={setCustomFeature}
                onBack={() => setStep('project')}
                onFinish={handleFinish}
              />
            )}

            {step === 'evaluation' &&
              selectedRole &&
              selectedRole !== 'other' && (
                <FeatureEvaluationStep
                  role={selectedRole}
                  environmentKey={environmentKey}
                  featureName={featureName}
                  projectName={projectName}
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
