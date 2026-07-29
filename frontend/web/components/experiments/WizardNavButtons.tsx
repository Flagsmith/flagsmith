import { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'

const STEP_SLUGS = ['setup', 'rollout', 'measurement', 'review'] as const

type WizardNavButtonsProps = {
  currentStep: number
  totalSteps: number
  canContinue: boolean
  isSubmitting?: boolean
  onBack: () => void
  onContinue: () => void
  onLaunch: () => void
}

const WizardNavButtons: FC<WizardNavButtonsProps> = ({
  canContinue,
  currentStep,
  isSubmitting,
  onBack,
  onContinue,
  onLaunch,
  totalSteps,
}) => {
  const isLastStep = currentStep === totalSteps - 1
  const stepSlug = STEP_SLUGS[currentStep] ?? currentStep

  return (
    <div className='d-flex justify-content-end gap-3 mt-4'>
      {currentStep > 0 && (
        <Button
          id={`experiment-wizard-${stepSlug}-back`}
          theme='outline'
          onClick={onBack}
        >
          <Icon name='arrow-left' width={16} />
          Back
        </Button>
      )}
      {isLastStep ? (
        <Button
          id='experiment-wizard-review-create'
          onClick={onLaunch}
          disabled={isSubmitting || !canContinue}
        >
          Create Experiment
          <Icon name='rocket' width={16} />
        </Button>
      ) : (
        <Button
          id={`experiment-wizard-${stepSlug}-continue`}
          onClick={onContinue}
          disabled={!canContinue}
        >
          Continue
        </Button>
      )}
    </div>
  )
}

export default WizardNavButtons
