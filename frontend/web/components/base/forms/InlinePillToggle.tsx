import React from 'react'
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
      {options.map((option) => (
        <button
          key={option.value}
          type='button'
          role='radio'
          aria-checked={value === option.value}
          data-test={dataTest ? `${dataTest}-${option.value}` : undefined}
          className={cn('inline-pill-toggle__option', {
            'inline-pill-toggle__option--active': value === option.value,
          })}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

export default InlinePillToggle
