import { FC } from 'react'
import Icon from 'components/icons/Icon'
import './WizardStepper.scss'

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
    subtitle: "Select how much traffic enters and how it's split",
    title: 'Rollout configuration',
  },
  {
    subtitle: 'Pick the metrics that determine success',
    title: 'Measurement',
  },
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

type StepStatus = 'done' | 'active' | 'upcoming'

const getStatus = (
  index: number,
  currentStep: number,
  completedSteps: Set<number>,
): StepStatus => {
  if (completedSteps.has(index) && index !== currentStep) return 'done'
  if (index === currentStep) return 'active'
  return 'upcoming'
}

const WizardStepper: FC<WizardStepperProps> = ({
  completedSteps,
  currentStep,
  onStepClick,
}) => {
  return (
    <nav className='wizard-sidebar'>
      {STEPS.map((step, index) => {
        const status = getStatus(index, currentStep, completedSteps)
        const isClickable = status === 'done'
        const showConnector = index < STEPS.length - 1

        return (
          <div
            key={index}
            className={`wizard-step wizard-step--${status}`}
            onClick={isClickable ? () => onStepClick(index) : undefined}
            role={isClickable ? 'button' : undefined}
            tabIndex={isClickable ? 0 : undefined}
            onKeyDown={
              isClickable
                ? (e) => {
                    if (e.key === 'Enter' || e.key === ' ') onStepClick(index)
                  }
                : undefined
            }
          >
            <div className='wizard-step__left'>
              <div className='wizard-step__circle'>
                {status === 'done' ? (
                  <Icon name='checkmark-circle' width={16} />
                ) : (
                  <span className='wizard-step__number'>{index + 1}</span>
                )}
              </div>
              {showConnector && <div className='wizard-step__connector' />}
            </div>

            <div className='wizard-step__right'>
              <div className='wizard-step__header'>
                <span className='wizard-step__title'>{step.title}</span>
                {status === 'done' && (
                  <span className='wizard-step__badge'>Complete</span>
                )}
              </div>
              <span className='wizard-step__subtitle'>{step.subtitle}</span>
            </div>
          </div>
        )
      })}
    </nav>
  )
}

export default WizardStepper
