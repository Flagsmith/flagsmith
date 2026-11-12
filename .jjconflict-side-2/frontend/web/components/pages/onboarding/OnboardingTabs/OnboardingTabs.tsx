import React, { KeyboardEvent, ReactNode, useRef } from 'react'
import OnboardingTabButton from './OnboardingTabButton'
import './OnboardingTabs.scss'

export type OnboardingTab<Id extends string = string> = {
  id: Id
  label: ReactNode
  // Pushes this tab to the trailing edge of the row (via ms-auto).
  alignEnd?: boolean
}

type OnboardingTabsProps<Id extends string> = {
  tabs: OnboardingTab<Id>[]
  activeId: Id
  onChange: (id: Id) => void
  'aria-label': string
}

// One-off tablist for the onboarding connect panel. We deliberately don't reuse
// the shared navigation Tabs because this design right-aligns one tab ("Connect
// with AI"), which the shared component can't express - it packs tabs left and
// reserves the right slot for a CTA. It's local to onboarding by design.
//
// Behaviour follows the WAI-ARIA tabs pattern: role tablist/tab, aria-selected,
// roving tabindex, and Arrow/Home/End keys with selection following focus. The
// list owns the refs + key handling; pair it with OnboardingTabPanel for the
// content side.
function OnboardingTabs<Id extends string>({
  activeId,
  'aria-label': ariaLabel,
  onChange,
  tabs,
}: OnboardingTabsProps<Id>) {
  const buttonRefs = useRef<(HTMLButtonElement | null)[]>([])

  const onKeyDown = (e: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const last = tabs.length - 1
    let next: number
    switch (e.key) {
      case 'ArrowRight':
        next = index === last ? 0 : index + 1
        break
      case 'ArrowLeft':
        next = index === 0 ? last : index - 1
        break
      case 'Home':
        next = 0
        break
      case 'End':
        next = last
        break
      default:
        return
    }
    e.preventDefault()
    onChange(tabs[next].id)
    buttonRefs.current[next]?.focus()
  }

  return (
    <div
      role='tablist'
      aria-label={ariaLabel}
      className='onboarding-tabs d-flex align-items-center gap-2'
    >
      {tabs.map((tab, index) => (
        <OnboardingTabButton
          key={tab.id}
          ref={(el) => {
            buttonRefs.current[index] = el
          }}
          id={tab.id}
          label={tab.label}
          alignEnd={tab.alignEnd}
          selected={tab.id === activeId}
          onSelect={() => onChange(tab.id)}
          onKeyDown={(e) => onKeyDown(e, index)}
        />
      ))}
    </div>
  )
}

export default OnboardingTabs
