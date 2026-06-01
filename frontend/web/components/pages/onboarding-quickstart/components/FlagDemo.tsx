import React, { FC, useState } from 'react'
import Switch from 'components/Switch'
import Icon from 'components/icons/Icon'
import CodeSnippet from 'web/components/pages/onboarding-quickstart/components/CodeSnippet'
import SampleAppPreview from 'web/components/pages/onboarding-quickstart/components/SampleAppPreview'
import 'web/components/pages/onboarding-quickstart/components/FlagDemo.scss'

type FlagDemoProps = {
  environmentKey: string
  featureName: string
  defaultEnabled?: boolean
  onToggle?: (enabled: boolean) => void
}

/**
 * The shared "see your flag work" AHA: the SDK snippet, a live sample app the
 * flag controls, and a toggle — the whole flag loop in one view. Context-
 * agnostic: it takes the flag inputs and emits a toggle event; the host (the
 * stepped flow's final step, or the single-page onboarding) owns the framing
 * and any surrounding CTAs.
 *
 * v1 is simulated — the toggle drives local state so the demo is instant and
 * needs no backend. The interface is unchanged when this is upgraded to a real
 * SDK evaluation against the user's environment.
 */
const FlagDemo: FC<FlagDemoProps> = ({
  defaultEnabled = true,
  environmentKey,
  featureName,
  onToggle,
}) => {
  const [enabled, setEnabled] = useState(defaultEnabled)

  const handleToggle = () => {
    setEnabled((value) => {
      const next = !value
      onToggle?.(next)
      return next
    })
  }

  return (
    <div className='flag-demo'>
      <div className='flag-demo__stage'>
        <div className='flag-demo__panel'>
          <CodeSnippet
            environmentKey={environmentKey}
            featureName={featureName}
          />
        </div>
        <div className='flag-demo__panel'>
          <SampleAppPreview enabled={enabled} featureName={featureName} />
        </div>
      </div>

      <div className='flag-demo__control rounded-lg border border-default bg-surface-default p-3 d-flex flex-column gap-2'>
        <div className='d-flex align-items-center gap-3'>
          <span className='text-muted'>Your flag</span>
          <code className='text-action'>{featureName}</code>
          <div className='ms-auto d-flex align-items-center gap-2'>
            <span className='text-muted'>{enabled ? 'On' : 'Off'}</span>
            <Switch
              checked={enabled}
              onChange={handleToggle}
              aria-label={`Toggle ${featureName}`}
            />
          </div>
        </div>
        <div
          className={`d-flex align-items-center gap-2 ${
            enabled ? 'text-success' : 'text-muted'
          }`}
        >
          {enabled && <Icon name='checkmark' width={16} />}
          <span>
            {enabled
              ? 'Changed live — no deploy needed'
              : 'Toggle the flag to show the feature'}
          </span>
        </div>
      </div>
    </div>
  )
}

export default FlagDemo
