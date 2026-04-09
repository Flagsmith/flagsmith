import React, { FC } from 'react'
import Icon from 'components/icons/Icon'
import { WizardStepStatus } from 'components/experiments-v2/types'
import './WizardStepIndicator.scss'

type WizardStepIndicatorProps = {
  stepNumber: number
  title: string
  subtitle?: string
  status: WizardStepStatus
  completeSummary?: string
  showConnector?: boolean
  onClick?: () => void
}

const WizardStepIndicator: FC<WizardStepIndicatorProps> = ({
  completeSummary,
  onClick,
  showConnector = true,
  status,
  stepNumber,
  subtitle,
  title,
}) => {
  const isClickable = status === 'done' && !!onClick

  return (
    <div
      className={`wizard-step-indicator wizard-step-indicator--${status}`}
      onClick={isClickable ? onClick : undefined}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={
        isClickable
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') onClick?.()
            }
          : undefined
      }
    >
      <div className='wizard-step-indicator__left'>
        <div className='wizard-step-indicator__circle'>
          {status === 'done' ? (
            <Icon name='checkmark-circle' width={16} />
          ) : (
            <span className='wizard-step-indicator__number'>{stepNumber}</span>
          )}
        </div>
        {showConnector && <div className='wizard-step-indicator__connector' />}
      </div>

      <div className='wizard-step-indicator__right'>
        <div className='wizard-step-indicator__header'>
          <span className='wizard-step-indicator__title'>{title}</span>
          {status === 'done' && (
            <span className='wizard-step-indicator__badge'>Complete</span>
          )}
        </div>
        {status === 'done' && completeSummary && (
          <span className='wizard-step-indicator__summary'>
            {completeSummary}
          </span>
        )}
        {status === 'active' && subtitle && (
          <span className='wizard-step-indicator__description'>{subtitle}</span>
        )}
        {status === 'upcoming' && subtitle && (
          <span className='wizard-step-indicator__subtitle'>{subtitle}</span>
        )}
      </div>
    </div>
  )
}

WizardStepIndicator.displayName = 'WizardStepIndicator'
export default WizardStepIndicator
