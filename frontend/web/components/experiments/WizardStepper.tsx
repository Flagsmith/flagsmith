import { FC } from 'react'
import { IonIcon } from '@ionic/react'
import { checkmarkCircle } from 'ionicons/icons'
import cn from 'classnames'

type StepDef = {
  title: string
  subtitle: string
}

const STEPS: StepDef[] = [
  {
    subtitle: 'Name, hypothesis, and the flag to experiment on',
    title: 'Setup',
  },
  {
    subtitle: 'Choose who is exposed and how traffic is split',
    title: 'Audience & Traffic',
  },
  { subtitle: 'Pick the metrics that determine success', title: 'Measurement' },
  {
    subtitle: 'Review your configuration and launch',
    title: 'Review & Launch',
  },
]

type WizardStepperProps = {
  currentStep: number
  completedSteps: Set<number>
  onStepClick: (step: number) => void
}

const WizardStepper: FC<WizardStepperProps> = ({
  completedSteps,
  currentStep,
  onStepClick,
}) => {
  return (
    <div
      className='d-flex flex-column gap-3'
      style={{ flexShrink: 0, width: 220 }}
    >
      {STEPS.map((step, index) => {
        const isActive = index === currentStep
        const isCompleted = completedSteps.has(index)
        const isClickable = isCompleted || index < currentStep

        return (
          <button
            key={index}
            type='button'
            className={cn(
              'd-flex align-items-start gap-2 bg-transparent border-0 p-0 text-start',
              {
                'cursor-pointer': isClickable,
                'opacity-50': !isActive && !isCompleted,
              },
            )}
            disabled={!isClickable && !isActive}
            onClick={() => isClickable && onStepClick(index)}
          >
            <div className='flex-shrink-0 mt-1'>
              {isCompleted ? (
                <IonIcon
                  icon={checkmarkCircle}
                  className='text-success'
                  style={{ fontSize: 24 }}
                />
              ) : (
                <div
                  className={cn(
                    'd-flex align-items-center justify-content-center rounded-circle',
                    isActive ? 'bg-primary text-white' : 'border text-muted',
                  )}
                  style={{ fontSize: 12, height: 24, width: 24 }}
                >
                  {index + 1}
                </div>
              )}
            </div>
            <div>
              <div className={cn('fw-bold', { 'text-primary': isActive })}>
                {step.title}
                {isCompleted && (
                  <span className='text-success ms-2' style={{ fontSize: 12 }}>
                    Complete
                  </span>
                )}
              </div>
              <div className='text-muted' style={{ fontSize: 12 }}>
                {step.subtitle}
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}

export default WizardStepper
