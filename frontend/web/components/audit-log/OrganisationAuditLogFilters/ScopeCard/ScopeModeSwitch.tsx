import { FC, KeyboardEvent, useRef } from 'react'
import { AuditLogScopeFilter } from 'components/audit-log/auditLogScopeFilter'
import BareButton from 'components/base/forms/BareButton'

const ARROW_STEPS: Record<string, number> = {
  ArrowDown: 1,
  ArrowLeft: -1,
  ArrowRight: 1,
  ArrowUp: -1,
}

export type ScopeMode = AuditLogScopeFilter['type']

type ScopeModeSwitchProps = {
  options: { value: ScopeMode; label: string }[]
  value: ScopeMode
  onChange: (value: ScopeMode) => void
}

// A radio group: Tab reaches the checked option, arrow keys move and select.
const ScopeModeSwitch: FC<ScopeModeSwitchProps> = ({
  onChange,
  options,
  value,
}) => {
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
      aria-label='Scope type'
      className='scope-mode-switch d-flex p-1 rounded-md bg-surface-muted'
      onKeyDown={onKeyDown}
    >
      {options.map((option, i) => (
        <BareButton
          key={option.value}
          ref={(el) => {
            refs.current[i] = el
          }}
          role='radio'
          aria-checked={i === index}
          tabIndex={i === index ? 0 : -1}
          className='scope-mode-switch__option justify-content-center rounded-sm fw-semibold fs-caption'
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </BareButton>
      ))}
    </div>
  )
}

export default ScopeModeSwitch
