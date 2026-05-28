import React, { FC, useRef } from 'react'
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
  const optionRefs = useRef<(HTMLButtonElement | null)[]>([])

  // WAI-ARIA radiogroup roving tabindex: only the selected option is in
  // the tab sequence (or the first option if nothing's selected yet).
  // Arrow keys move both selection and focus between options.
  const selectedIndex = ONBOARDING_ROLES.findIndex((r) => r.key === value)
  const tabbableIndex = selectedIndex === -1 ? 0 : selectedIndex

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) => {
    let nextIndex: number | null = null
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
      // First arrow press with no selection yet picks the currently-
      // focused option (option 0 on initial mount) instead of skipping
      // past it. Subsequent presses advance normally.
      nextIndex =
        selectedIndex === -1 ? index : (index + 1) % ONBOARDING_ROLES.length
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
      nextIndex =
        selectedIndex === -1
          ? index
          : (index - 1 + ONBOARDING_ROLES.length) % ONBOARDING_ROLES.length
    } else if (e.key === 'Home') {
      nextIndex = 0
    } else if (e.key === 'End') {
      nextIndex = ONBOARDING_ROLES.length - 1
    } else if (e.key === 'Enter' && selectedIndex !== -1) {
      // Enter on a focused option with a selection in place advances to
      // the next step — saves a Tab + Enter to reach the Next button.
      e.preventDefault()
      onNext()
      return
    }
    if (nextIndex !== null) {
      e.preventDefault()
      onChange(ONBOARDING_ROLES[nextIndex].key)
      optionRefs.current[nextIndex]?.focus()
    }
  }

  return (
    <StepShell
      title="What's your role?"
      subtitle="We'll tailor what you see next based on what you're trying to do."
      body={
        <div
          role='radiogroup'
          aria-label="What's your role?"
          className='d-flex flex-column gap-2'
        >
          {ONBOARDING_ROLES.map((role, index) => {
            const isSelected = value === role.key
            return (
              <button
                ref={(el) => {
                  optionRefs.current[index] = el
                }}
                type='button'
                role='radio'
                aria-checked={isSelected}
                tabIndex={index === tabbableIndex ? 0 : -1}
                key={role.key}
                onClick={() => onChange(role.key)}
                onKeyDown={(e) => handleKeyDown(e, index)}
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
