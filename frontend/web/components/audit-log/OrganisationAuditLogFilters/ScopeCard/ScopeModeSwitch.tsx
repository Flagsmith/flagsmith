import { FC, KeyboardEvent, useRef } from 'react'
import { AuditLogScopeFilter } from 'components/audit-log/auditLogScopeFilter'
import BareButton from 'components/base/forms/BareButton'
import { getArrowTarget } from './arrowTarget'

export type ScopeMode = AuditLogScopeFilter['type']

type ScopeModeSwitchProps = {
  options: { value: ScopeMode; label: string }[]
  value: ScopeMode
  onChange: (value: ScopeMode) => void
}

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
    const next = getArrowTarget(e.key, index, options.length)
    if (next === null) return
    e.preventDefault()
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
