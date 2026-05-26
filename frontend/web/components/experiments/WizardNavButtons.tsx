import { FC } from 'react'
import Button from 'components/base/forms/Button'
import { IonIcon } from '@ionic/react'
import { arrowBack, rocketOutline } from 'ionicons/icons'

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

  return (
    <div className='d-flex justify-content-end gap-3 mt-4'>
      {currentStep > 0 && (
        <Button theme='outline' onClick={onBack}>
          <IonIcon icon={arrowBack} className='me-1' />
          Back
        </Button>
      )}
      {isLastStep ? (
        <Button onClick={onLaunch} disabled={isSubmitting}>
          Create Experiment
          <IonIcon icon={rocketOutline} className='ms-1' />
        </Button>
      ) : (
        <Button onClick={onContinue} disabled={!canContinue}>
          Continue
        </Button>
      )}
    </div>
  )
}

export default WizardNavButtons
