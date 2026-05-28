import React, { FC, useEffect, useState } from 'react'
import Button from 'components/base/forms/Button'
import Constants from 'common/constants'
import StatusPanel from 'web/components/pages/onboarding-quickstart/components/StatusPanel'
import SuccessActions from 'web/components/pages/onboarding-quickstart/components/SuccessActions'
import CodeSnippet from 'web/components/pages/onboarding-quickstart/components/CodeSnippet'
import { OnboardingRoleKey } from 'web/components/pages/onboarding-quickstart/data/roles'
import { useFirstEvaluationPoll } from 'web/components/pages/onboarding-quickstart/hooks/useFirstEvaluationPoll'

type FeatureEvaluationStepProps = {
  environmentKey: string
  featureName: string
  onExplore: () => void
  onFirstEvalReceived?: () => void
  onInvite: () => void
  projectName: string
  role: Exclude<OnboardingRoleKey, 'other'>
}

// Curated subset of integrations shown to PMs at the "see it work"
// moment — the goal is a visual capability check ("Flagsmith plugs into
// the tools we use"), not a full integration-selection wizard. The full
// picker lives at `components/IntegrationSelect.tsx` for the post-onboarding
// surface.
const PM_INTEGRATION_TITLES = [
  'Slack',
  'GitHub',
  'Datadog',
  'Jira',
  'Segment',
  'Amplitude',
  'New Relic',
  'Google Analytics',
]

const FeatureEvaluationStep: FC<FeatureEvaluationStepProps> = ({
  environmentKey,
  featureName,
  onExplore,
  onFirstEvalReceived,
  onInvite,
  projectName,
  role,
}) => {
  const { markReceived, state } = useFirstEvaluationPoll({ enabled: true })
  const [toggleValue, setToggleValue] = useState(false)
  const isReceived = state === 'received'

  useEffect(() => {
    if (state === 'received') {
      onFirstEvalReceived?.()
    }
  }, [state, onFirstEvalReceived])

  if (role === 'pm') {
    // PM path: skip the SDK install entirely. Show the integration grid
    // as a visible capability check, then route through invite-an-engineer.
    const integrations = Constants.integrationSummaries.filter((i) =>
      PM_INTEGRATION_TITLES.includes(i.title),
    )
    return (
      <div className='onboarding-quickstart__panel d-flex flex-column gap-3'>
        <div>
          <h2 className='mb-1'>Your dashboard is ready</h2>
          <p className='mb-0'>
            <code className='text-default'>{projectName}</code> and{' '}
            <code className='text-default'>{featureName}</code> are set up.
            Flagsmith plugs into the tools your team already uses — invite an
            engineer to wire it into your codebase.
          </p>
        </div>

        <div>
          <h4 className='mb-2'>Works with your stack</h4>
          <ul className='onboarding-quickstart__integrations list-unstyled m-0 p-0 d-grid gap-2'>
            {integrations.map((integration) => (
              <li
                key={integration.title}
                className='onboarding-quickstart__integration rounded-md border border-default bg-surface-default p-3 d-flex align-items-center gap-2'
              >
                <img
                  src={integration.image}
                  alt=''
                  width={20}
                  height={20}
                  className='onboarding-quickstart__integration-logo'
                />
                <span className='text-default'>{integration.title}</span>
              </li>
            ))}
          </ul>
        </div>

        <SuccessActions onExplore={onExplore} onInvite={onInvite} role={role} />
      </div>
    )
  }

  // Engineer path (default): SDK snippet + status panel + first-eval poll.
  return (
    <div className='onboarding-quickstart__panel d-flex flex-column gap-3'>
      <div>
        <h2 className='mb-1'>Let's get your first flag working</h2>
        <p className='mb-0'>
          <code className='text-default'>{projectName}</code> and{' '}
          <code className='text-default'>{featureName}</code> are ready from
          your answers. Paste the snippet below, run your app, watch the status
          flip green, then toggle the flag.
        </p>
      </div>

      <StatusPanel
        featureName={featureName}
        isReceived={isReceived}
        onToggle={() => setToggleValue((value) => !value)}
        toggleValue={toggleValue}
      />

      <div>
        <h4 className='mb-2'>Paste this in your app</h4>
        <CodeSnippet
          environmentKey={environmentKey}
          featureName={featureName}
        />
      </div>

      {isReceived && (
        <SuccessActions onExplore={onExplore} onInvite={onInvite} role={role} />
      )}

      {!isReceived && (
        <div className='d-flex justify-content-end'>
          <Button theme='text' onClick={markReceived}>
            I've installed it — continue
          </Button>
        </div>
      )}
    </div>
  )
}

export default FeatureEvaluationStep
