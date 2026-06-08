import React, { FC } from 'react'
import Icon from 'components/icons/Icon'
import './OnboardingChip.scss'

type OnboardingChipProps = {
  completedCount: number
  isPulsing: boolean
  label?: string
  onClick: () => void
  totalCount: number
}

const OnboardingChip: FC<OnboardingChipProps> = ({
  completedCount,
  isPulsing,
  label = 'Getting Started',
  onClick,
  totalCount,
}) => (
  <button
    type='button'
    onClick={onClick}
    className='onboarding-chip d-inline-flex align-items-center gap-2 px-2 py-1 rounded-full border border-default bg-surface-default'
  >
    <span
      className={`onboarding-chip__dot ${
        isPulsing ? 'onboarding-chip__dot--pulsing' : ''
      }`}
      aria-hidden='true'
    />
    <span className='onboarding-chip__label d-none d-md-inline text-default'>
      {label}
    </span>
    <span className='onboarding-chip__counter text-muted'>
      {completedCount}/{totalCount}
    </span>
    <Icon name='rocket' width={14} />
  </button>
)

export default OnboardingChip
