import { KeyboardEvent, useRef } from 'react'
import classNames from 'classnames'

const ARROW_STEPS: Record<string, number> = {
  ArrowDown: 1,
  ArrowLeft: -1,
  ArrowRight: 1,
  ArrowUp: -1,
}

export type ScopeModeOption<T extends string> = {
  value: T
  label: string
}

export type ScopeModeSwitchProps<T extends string> = {
  options: ScopeModeOption<T>[]
  value: T
  onChange: (value: T) => void
  'aria-label': string
  className?: string
}

// A radio group: Tab reaches the checked option, arrow keys move and select.
const ScopeModeSwitch = <T extends string>({
  'aria-label': ariaLabel,
  className,
  onChange,
  options,
  value,
}: ScopeModeSwitchProps<T>) => {
  const refs = useRef<(HTMLButtonElement | null)[]>([])
  const index = Math.max(
    0,
    options.findIndex((o) => o.value === value),
  )

  const onKeyDown = (e: KeyboardEvent) => {
    const step = ARROW_STEPS[e.key]
    if (!step) return
    e.preventDefault()
    const next = (index + step + options.length) % options.length
    onChange(options[next].value)
    refs.current[next]?.focus()
  }

  return (
    <div
      role='radiogroup'
      aria-label={ariaLabel}
      className={classNames(
        'scope-mode-switch d-flex p-1 rounded-md bg-surface-muted',
        className,
      )}
      onKeyDown={onKeyDown}
    >
      {options.map((option, i) => (
        <button
          key={option.value}
          ref={(el) => {
            refs.current[i] = el
          }}
          type='button'
          role='radio'
          aria-checked={i === index}
          tabIndex={i === index ? 0 : -1}
          className='scope-mode-switch__option border-0 rounded-sm fw-semibold fs-caption'
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

export default ScopeModeSwitch
