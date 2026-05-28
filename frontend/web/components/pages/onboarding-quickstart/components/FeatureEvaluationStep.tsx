import React, { FC, useEffect, useMemo, useState } from 'react'
import { uniqBy } from 'lodash'
import Button from 'components/base/forms/Button'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import { IntegrationSummary } from 'components/pages/IntegrationsPage'
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

  // Same data merge as `components/IntegrationSelect.tsx` — Flagsmith
  // remote-config flag (`integration_data`) concatenated with the
  // hardcoded constants list, deduped by title. Read-only render here:
  // PM AHA is a visual capability check, not an interactive picker.
  // (`IntegrationSelect` itself currently lets users "select" tools
  // but doesn't connect anything — separate product gap, tracked
  // outside this work.)
  const pmIntegrations = useMemo(() => {
    if (role !== 'pm') return []
    const remote = Utils.getFlagsmithValue('integration_data')
    if (typeof remote !== 'string' || !remote) {
      return Constants.integrationSummaries.slice(0, 12)
    }
    const merged = uniqBy(
      Object.values(JSON.parse(remote)).concat(
        Constants.integrationSummaries,
      ) as IntegrationSummary[],
      (v) => v.title.toLowerCase(),
    )
    return merged.slice(0, 12)
  }, [role])

  useEffect(() => {
    if (state === 'received') {
      onFirstEvalReceived?.()
    }
  }, [state, onFirstEvalReceived])

  if (role === 'pm') {
    return (
      <div className='onboarding-quickstart__panel d-flex flex-column gap-3'>
        <div>
          <h2 className='mb-1'>Your dashboard is ready</h2>
          <p className='mb-0'>
            <code className='text-default'>{projectName}</code> and{' '}
            <code className='text-default'>{featureName}</code> are set up.
            Flagsmith plugs into the tools your team already uses — invite a
            teammate to wire it into your codebase.
          </p>
        </div>

        <div>
          <h4 className='mb-2'>Works with your stack</h4>
          <ul className='onboarding-quickstart__integrations list-unstyled m-0 p-0 d-grid gap-2'>
            {pmIntegrations.map((integration) => (
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
