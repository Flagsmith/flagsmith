import React, { FC } from 'react'
import classNames from 'classnames'
import './OnboardingTerminal.scss'

export type OnboardingTerminalProps = {
  featureName: string
  installCopied: boolean
  snippetCopied: boolean
  // First evaluation received (#7767).
  connected: boolean
}

// Verify console. Always dark (a terminal reads the same in both modes), so it
// uses a literal palette rather than theme tokens.
const OnboardingTerminal: FC<OnboardingTerminalProps> = ({
  connected,
  featureName,
  installCopied,
  snippetCopied,
}) => {
  const steps = [
    { done: installCopied, label: 'Copy install command' },
    { done: snippetCopied, label: 'Copy code snippet' },
    { done: connected, label: `First evaluation of '${featureName}'` },
  ]
  // The first unfinished step is the active one (amber).
  const currentIndex = steps.findIndex((step) => !step.done)

  return (
    <div className='onboarding-terminal'>
      <div className='onboarding-terminal__bar d-flex align-items-center gap-2'>
        <span className='onboarding-terminal__dot onboarding-terminal__dot--red' />
        <span className='onboarding-terminal__dot onboarding-terminal__dot--amber' />
        <span className='onboarding-terminal__dot onboarding-terminal__dot--green' />
        <span className='onboarding-terminal__title'>
          flagsmith — sdk console
        </span>
        <span
          className={classNames(
            'onboarding-terminal__badge d-inline-flex align-items-center gap-1 ms-auto',
            {
              'onboarding-terminal__badge--listening': !connected,
              'onboarding-terminal__badge--live': connected,
            },
          )}
        >
          <span className='onboarding-terminal__badge-dot' />
          {connected ? 'LIVE' : 'LISTENING'}
        </span>
      </div>

      <div
        className='onboarding-terminal__body d-flex flex-column gap-2'
        aria-live='polite'
      >
        {!connected && (
          <p className='onboarding-terminal__line onboarding-terminal__line--muted'>
            awaiting first request
          </p>
        )}
        {steps.map((step, index) => (
          <p
            key={step.label}
            className={classNames('onboarding-terminal__line', {
              'onboarding-terminal__line--current':
                !step.done && index === currentIndex,
              'onboarding-terminal__line--ok': step.done,
            })}
          >
            {step.done ? '[✓]' : '[ ]'} {step.label}
            {!step.done && index === steps.length - 1 ? '…' : ''}
          </p>
        ))}
        {connected ? (
          <>
            <p className='onboarding-terminal__line onboarding-terminal__line--dim'>
              SDK initialized · flags loaded · {featureName}: true
            </p>
            <p className='onboarding-terminal__line onboarding-terminal__line--ok onboarding-terminal__line--strong'>
              ✓ Connected
            </p>
            <p className='onboarding-terminal__line onboarding-terminal__line--ok'>
              ✓ {featureName} is live
            </p>
          </>
        ) : (
          <p className='onboarding-terminal__line onboarding-terminal__line--prompt'>
            $ <span className='onboarding-terminal__cursor' aria-hidden />
          </p>
        )}
      </div>
    </div>
  )
}

export default OnboardingTerminal
