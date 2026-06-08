import React, { FC, useMemo, useState } from 'react'
import { uniqBy } from 'lodash'
import Constants from 'common/constants'
import Utils, { planNames } from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import { IntegrationSummary } from 'components/pages/IntegrationsPage'
import SuccessActions from 'web/components/pages/onboarding-quickstart/components/SuccessActions'
import FlagDemo from 'web/components/pages/onboarding-quickstart/components/FlagDemo'
import { OnboardingRoleKey } from 'web/components/pages/onboarding-quickstart/data/roles'

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
  // Fire the activation callback the first time the user flips the demo flag —
  // the toggle is the AHA in this simulated v1 (there's no real signal yet).
  const [demoToggled, setDemoToggled] = useState(false)
  const handleDemoToggle = () => {
    if (!demoToggled) {
      setDemoToggled(true)
      onFirstEvalReceived?.()
    }
  }

  // Only surface "Invite a teammate" where it makes sense: self-hosted (any
  // plan) or paid SaaS. On the free SaaS plan we hide it rather than nudge an
  // upgrade, which would just be friction at this moment.
  const canInvite =
    !Utils.isSaas() ||
    Utils.getPlanName(AccountStore.getActiveOrgPlan()) !== planNames.free

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

  if (role === 'pm') {
    return (
      <div className='onboarding-quickstart__panel d-flex flex-column gap-3'>
        <div>
          <h2 className='mb-1'>Your dashboard is ready</h2>
          <p className='mb-0'>
            <code className='text-default'>{projectName}</code> and{' '}
            <code className='text-default'>{featureName}</code> are set up.
            Flagsmith plugs into the tools your team already uses
            {canInvite
              ? ' — invite a teammate to wire it into your codebase.'
              : '.'}
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

        <SuccessActions
          canInvite={canInvite}
          onExplore={onExplore}
          onInvite={onInvite}
          role={role}
        />
      </div>
    )
  }

  // Engineer path (default): the shared flag demo — code, a live sample app
  // the flag controls, and a toggle — then the success actions.
  return (
    <div className='onboarding-quickstart__panel d-flex flex-column gap-3'>
      <div>
        <h2 className='mb-1'>See your flag in action</h2>
        <p className='mb-0'>
          <code className='text-default'>{featureName}</code> is live in{' '}
          <code className='text-default'>{projectName}</code>. Flip it below and
          watch the app react — then paste the snippet to do the same in your
          own app.
        </p>
      </div>

      <FlagDemo
        environmentKey={environmentKey}
        featureName={featureName}
        onToggle={handleDemoToggle}
      />

      <SuccessActions
        canInvite={canInvite}
        onExplore={onExplore}
        onInvite={onInvite}
        role={role}
      />
    </div>
  )
}

export default FeatureEvaluationStep
