import React, { FC } from 'react'
import Icon from 'components/icons/Icon'
import Switch from 'components/Switch'

type StatusPanelProps = {
  featureName: string
  isReceived: boolean
  onToggle?: () => void
  toggleValue: boolean
}

const StatusPanel: FC<StatusPanelProps> = ({
  featureName,
  isReceived,
  onToggle,
  toggleValue,
}) => {
  const statusClass = isReceived
    ? 'onboarding-quickstart__status--received bg-surface-success border-success'
    : 'onboarding-quickstart__status--waiting bg-surface-warning border-warning'

  // Eval count is stubbed for the POC — backend signal not yet wired.
  const statusLabel = isReceived
    ? 'First request received · 3 evaluations in last minute'
    : 'Waiting for first request from your app…'

  // `text-warning` / `text-success` semantic tokens fail contrast against
  // their own tinted surfaces, so this panel uses the locally-defined
  // *-strong text rules in OnboardingQuickstartPage.scss.
  const statusTextClass = isReceived
    ? 'onboarding-quickstart__status-text--received'
    : 'onboarding-quickstart__status-text--waiting'

  return (
    <div
      className={`onboarding-quickstart__status rounded-lg border p-4 ${statusClass}`}
    >
      <div className='d-flex align-items-center gap-2 mb-3'>
        <span
          className={`onboarding-quickstart__status-dot ${
            isReceived
              ? 'onboarding-quickstart__status-dot--solid'
              : 'onboarding-quickstart__status-dot--pulsing'
          }`}
          aria-hidden='true'
        />
        <span className={`fw-semibold ${statusTextClass}`}>{statusLabel}</span>
      </div>

      <div className='onboarding-quickstart__status-grid d-flex align-items-center justify-content-between gap-3 flex-wrap'>
        <div className='d-flex align-items-center gap-2 text-muted'>
          <span className='onboarding-quickstart__node rounded-md bg-surface-default border border-default px-3 py-2'>
            Your app
          </span>
          <Icon name='arrow-right' width={18} />
          <span className='onboarding-quickstart__node rounded-md bg-surface-default border border-default px-3 py-2'>
            Flagsmith
          </span>
        </div>

        <div className='d-flex align-items-center gap-2'>
          <code className='text-default'>{featureName}</code>
          <Switch
            checked={toggleValue}
            disabled={!isReceived}
            onChange={() => isReceived && onToggle?.()}
            aria-label={`Toggle ${featureName}`}
          />
        </div>
      </div>

      {!isReceived && (
        <p className='text-muted mt-3 mb-0'>
          Paste the snippet below and run your app — we'll detect the first
          request automatically.
        </p>
      )}
      {isReceived && (
        <p className='onboarding-quickstart__status-text--received mt-3 mb-0'>
          You're live. Flip the toggle above, then configure targeting, add
          segments, or roll out gradually whenever you're ready.
        </p>
      )}
    </div>
  )
}

export default StatusPanel
