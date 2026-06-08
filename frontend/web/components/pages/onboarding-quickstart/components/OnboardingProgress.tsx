import React, { CSSProperties, FC } from 'react'

export type OnboardingStepKey =
  | 'role'
  | 'org'
  | 'project'
  | 'feature'
  | 'evaluation'

export type OnboardingStepDef = {
  key: OnboardingStepKey
  title: string
}

type OnboardingProgressProps = {
  currentStep: OnboardingStepKey
  steps: OnboardingStepDef[]
}

/**
 * Slim progress bar — a deliberately lightweight indicator that reads as
 * "this is quick" rather than the heavier named-step list, which made the
 * 2-minute flow look like more work than it is. Reflects the real, variable
 * step count (the org and evaluation steps are skipped in some flows).
 */
const OnboardingProgress: FC<OnboardingProgressProps> = ({
  currentStep,
  steps,
}) => {
  const index = steps.findIndex((step) => step.key === currentStep)
  const current = Math.max(1, index + 1)
  const total = Math.max(steps.length, 1)
  const percent = Math.round((current / total) * 100)

  return (
    <div className='onboarding-quickstart__progress'>
      <div className='onboarding-quickstart__progress-label text-muted'>
        Step {current} of {total}
      </div>
      <div
        className='onboarding-quickstart__progress-track'
        role='progressbar'
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={current}
        aria-label={`Step ${current} of ${total}`}
        // Dynamic fill width has to be computed at runtime; expose it as a
        // custom property so the actual styling stays in the stylesheet.
        style={{ '--onboarding-progress': `${percent}%` } as CSSProperties}
      >
        <div className='onboarding-quickstart__progress-fill' />
      </div>
    </div>
  )
}

export default OnboardingProgress
