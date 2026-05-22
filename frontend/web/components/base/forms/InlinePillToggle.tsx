import React, { useRef } from 'react'
import cn from 'classnames'

type InlinePillToggleSize = 'small' | 'medium' | 'large'

type Option<T extends string> = {
  label: string
  value: T
}

type InlinePillToggleProps<T extends string> = {
  options: Option<T>[]
  value: T
  onChange: (value: T) => void
  size?: InlinePillToggleSize
  className?: string
  'data-test'?: string
}

function InlinePillToggle<T extends string>({
  className,
  'data-test': dataTest,
  onChange,
  options,
  size = 'medium',
  value,
}: InlinePillToggleProps<T>) {
  const buttonRefs = useRef<(HTMLButtonElement | null)[]>([])

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let next: number | null = null
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      next = (index + 1) % options.length
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      next = (index - 1 + options.length) % options.length
    }
    if (next !== null) {
      e.preventDefault()
      onChange(options[next].value)
      buttonRefs.current[next]?.focus()
    }
  }

  return (
    <div
      className={cn(
        'inline-pill-toggle',
        `inline-pill-toggle--${size}`,
        className,
      )}
      data-test={dataTest}
      role='radiogroup'
    >
      {options.map((option, index) => {
        const isActive = value === option.value
        return (
          <button
            key={option.value}
            ref={(el) => {
              buttonRefs.current[index] = el
            }}
            type='button'
            role='radio'
            aria-checked={isActive}
            tabIndex={isActive ? 0 : -1}
            data-test={dataTest ? `${dataTest}-${option.value}` : undefined}
            className={cn('inline-pill-toggle__option', {
              'inline-pill-toggle__option--active': isActive,
            })}
            onClick={() => onChange(option.value)}
            onKeyDown={(e) => handleKeyDown(e, index)}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}

export default InlinePillToggle
