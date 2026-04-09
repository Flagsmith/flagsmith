import React, { FC } from 'react'
import WizardStepIndicator from './WizardStepIndicator'
import {
  WizardStepDef,
  WizardStepStatus,
} from 'components/experiments-v2/types'
import './WizardSidebar.scss'

type WizardSidebarProps = {
  steps: WizardStepDef[]
  currentStep: number
  onStepClick?: (step: number) => void
}

function getStepStatus(index: number, currentStep: number): WizardStepStatus {
  if (index < currentStep) return 'done'
  if (index === currentStep) return 'active'
  return 'upcoming'
}

const WizardSidebar: FC<WizardSidebarProps> = ({
  currentStep,
  onStepClick,
  steps,
}) => {
  return (
    <nav className='wizard-sidebar'>
      {steps.map((step, index) => (
        <WizardStepIndicator
          key={index}
          stepNumber={index + 1}
          title={step.title}
          subtitle={step.subtitle}
          status={getStepStatus(index, currentStep)}
          completeSummary={step.completeSummary}
          showConnector={index < steps.length - 1}
          onClick={index < currentStep ? () => onStepClick?.(index) : undefined}
        />
      ))}
    </nav>
  )
}

WizardSidebar.displayName = 'WizardSidebar'
export default WizardSidebar
