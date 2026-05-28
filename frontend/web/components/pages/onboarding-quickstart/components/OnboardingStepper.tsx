import React, { FC } from 'react'
import Icon from 'components/icons/Icon'

export type OnboardingStepKey =
  | 'role'
  | 'org'
  | 'project'
  | 'feature'
  | 'evaluation'

type OnboardingStepStatus = 'done' | 'active' | 'upcoming'

export type OnboardingStepDef = {
  key: OnboardingStepKey
  title: string
}

type OnboardingStepperProps = {
  currentStep: OnboardingStepKey
  onStepClick?: (key: OnboardingStepKey) => void
  steps: OnboardingStepDef[]
}

const indexFor = (steps: OnboardingStepDef[], key: OnboardingStepKey): number =>
  steps.findIndex((step) => step.key === key)

const statusFor = (
  index: number,
  currentIndex: number,
): OnboardingStepStatus => {
  if (index < currentIndex) return 'done'
  if (index === currentIndex) return 'active'
  return 'upcoming'
}

const OnboardingStepper: FC<OnboardingStepperProps> = ({
  currentStep,
  onStepClick,
  steps,
}) => {
  const currentIndex = indexFor(steps, currentStep)

  return (
    <ol
      className='onboarding-stepper'
      aria-label='Onboarding progress'
      role='list'
    >
      {steps.map((step, index) => {
        const status = statusFor(index, currentIndex)
        const isClickable = status === 'done' && !!onStepClick
        const showConnector = index < steps.length - 1
        return (
          <li
            key={step.key}
            className={`onboarding-stepper__step onboarding-stepper__step--${status}`}
            aria-current={status === 'active' ? 'step' : undefined}
          >
            <button
              type='button'
              className='onboarding-stepper__node'
              onClick={isClickable ? () => onStepClick?.(step.key) : undefined}
              disabled={!isClickable}
            >
              <span className='onboarding-stepper__circle'>
                {status === 'done' ? (
                  <Icon name='checkmark' width={14} />
                ) : (
                  <span className='onboarding-stepper__number'>
                    {index + 1}
                  </span>
                )}
              </span>
              <span className='onboarding-stepper__title'>{step.title}</span>
            </button>
            {showConnector && (
              <span
                className='onboarding-stepper__connector'
                aria-hidden='true'
              />
            )}
          </li>
        )
      })}
    </ol>
  )
}

export default OnboardingStepper
