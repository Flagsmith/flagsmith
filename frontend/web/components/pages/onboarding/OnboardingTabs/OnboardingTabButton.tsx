import React, { KeyboardEvent, ReactNode, Ref } from 'react'
import classNames from 'classnames'

export type OnboardingTabButtonProps = {
  id: string
  label: ReactNode
  selected: boolean
  // Pushes the tab to the trailing edge of the row (via ms-auto).
  alignEnd?: boolean
  onSelect: () => void
  onKeyDown: (e: KeyboardEvent<HTMLButtonElement>) => void
  ref?: Ref<HTMLButtonElement>
}

// A single tab within OnboardingTabs. Roving tabindex and keyboard navigation
// are owned by the parent tablist (which holds the ref and the key handler);
// this just renders one role="tab" button wired to its panel by id.
const OnboardingTabButton = ({
  alignEnd,
  id,
  label,
  onKeyDown,
  onSelect,
  ref,
  selected,
}: OnboardingTabButtonProps) => (
  <button
    ref={ref}
    type='button'
    role='tab'
    id={id}
    aria-selected={selected}
    aria-controls={`${id}-panel`}
    tabIndex={selected ? 0 : -1}
    className={classNames('onboarding-tabs__tab', {
      'ms-auto': alignEnd,
      'onboarding-tabs__tab--active': selected,
    })}
    onClick={onSelect}
    onKeyDown={onKeyDown}
  >
    {label}
  </button>
)

export default OnboardingTabButton
