import React, { FC } from 'react'
import Switch from 'components/Switch'
import FeatureName from 'components/feature-summary/FeatureName'
import FeatureDescription from 'components/feature-summary/FeatureDescription'
import Tag from 'components/tags/Tag'

type OnboardingFlagTableProps = {
  featureName: string
  // Gated until the SDK's first request: the toggle only goes live once the
  // app is connected, so flipping it visibly changes the connected app.
  connected: boolean
  flagEnabled: boolean
  flagToggleDisabled?: boolean
  onToggleFlag: () => void
}

// The single demo flag rendered as a row in the real features-table, using the
// product's own components — FeatureName (name + copy button), Tag,
// FeatureDescription, Switch — so it's visually identical and can't drift
// from the product. We deliberately don't pull in the whole
// FeatureRow (coupled to stores, modals, permissions, the actions menu) or
// FeatureTags (health/overrides/stale machinery), none of which apply to a
// fresh onboarding flag. Env switcher + Create Feature are a fast-follow.
const OnboardingFlagTable: FC<OnboardingFlagTableProps> = ({
  connected,
  featureName,
  flagEnabled,
  flagToggleDisabled = false,
  onToggleFlag,
}) => (
  <div className='onboarding-single__flagtable-wrap'>
    <div
      className={`onboarding-single__flagtable rounded-lg${
        connected ? '' : ' onboarding-single__flagtable--locked'
      }`}
    >
      <div className='onboarding-single__flagtable-colhead d-flex align-items-center'>
        <span className='onboarding-single__flagtable-col onboarding-single__flagtable-col--feature'>
          Feature
        </span>
        <span className='onboarding-single__flagtable-col onboarding-single__flagtable-col--enabled'>
          Enabled
        </span>
      </div>

      <div className='onboarding-single__flagtable-row d-flex align-items-center'>
        <div className='onboarding-single__flagtable-feature'>
          <div className='onboarding-single__flagtable-nameline d-flex align-items-center'>
            <FeatureName name={featureName} />
            <Tag tag={{ color: '#27AB83', label: 'Onboarding' }} />
          </div>
          <FeatureDescription description='Controls the demo button shown to your users' />
        </div>
        <div className='onboarding-single__flagtable-enabled d-flex align-items-center'>
          <Switch
            checked={connected && flagEnabled}
            disabled={!connected || flagToggleDisabled}
            onChange={onToggleFlag}
            aria-label={`Toggle ${featureName}`}
          />
        </div>
      </div>
    </div>
  </div>
)

export default OnboardingFlagTable
