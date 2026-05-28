import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import StepShell from 'web/components/pages/onboarding-quickstart/components/StepShell'
import {
  ONBOARDING_ROLES,
  OnboardingRoleKey,
} from 'web/components/pages/onboarding-quickstart/data/roles'

type RoleStepProps = {
  onChange: (role: OnboardingRoleKey) => void
  onNext: () => void
  value: OnboardingRoleKey | null
}

const RoleStep: FC<RoleStepProps> = ({ onChange, onNext, value }) => {
  const isValid = !!value

  return (
    <StepShell
      title="What's your role?"
      subtitle="We'll tailor what you see next based on what you're trying to do."
      body={
        <div className='d-flex flex-column gap-2'>
          {ONBOARDING_ROLES.map((role) => {
            const isSelected = value === role.key
            return (
              <button
                type='button'
                key={role.key}
                onClick={() => onChange(role.key)}
                className={`onboarding-quickstart__radio-row w-100 text-start p-3 rounded-md border ${
                  isSelected
                    ? 'border-action bg-surface-action-subtle'
                    : 'border-default bg-surface-default'
                }`}
              >
                <span
                  className={`onboarding-quickstart__radio-dot ${
                    isSelected ? 'onboarding-quickstart__radio-dot--on' : ''
                  }`}
                  aria-hidden='true'
                />
                <span className='ms-2 text-default'>{role.title}</span>
              </button>
            )
          })}
        </div>
      }
      footer={
        <>
          <span />
          <Button theme='primary' onClick={onNext} disabled={!isValid}>
            Next →
          </Button>
        </>
      }
    />
  )
}

export default RoleStep
