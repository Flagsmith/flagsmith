import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import { IconName } from 'components/icons/Icon'
import './WizardNavButtons.scss'

type WizardNavButtonsProps = {
  onBack?: () => void
  onContinue: () => void
  isFirstStep?: boolean
  isLastStep?: boolean
  continueDisabled?: boolean
  continueLabel?: string
  continueIcon?: IconName
}

const WizardNavButtons: FC<WizardNavButtonsProps> = ({
  continueDisabled = false,
  continueIcon,
  continueLabel,
  isFirstStep = false,
  isLastStep = false,
  onBack,
  onContinue,
}) => {
  const label = continueLabel || (isLastStep ? 'Launch Experiment' : 'Continue')
  const icon = continueIcon || (isLastStep ? 'rocket' : undefined)

  return (
    <div className='wizard-nav-buttons'>
      {!isFirstStep && onBack && (
        <Button
          theme='outline'
          onClick={onBack}
          iconLeft='arrow-left'
          iconSize={16}
        >
          Back
        </Button>
      )}
      <Button
        theme='primary'
        onClick={onContinue}
        disabled={continueDisabled}
        iconRight={icon}
        iconSize={16}
      >
        {label}
      </Button>
    </div>
  )
}

WizardNavButtons.displayName = 'WizardNavButtons'
export default WizardNavButtons
