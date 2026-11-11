import { KeyboardEvent, useRef } from 'react'
import classNames from 'classnames'
import './SegmentedControl.scss'

export type SegmentedControlOption<T extends string> = {
  value: T
  label: string
}

export type SegmentedControlProps<T extends string> = {
  options: SegmentedControlOption<T>[]
  value: T
  onChange: (value: T) => void
  'aria-label': string
  className?: string
}

// One choice from two to five, all visible. A radio group: Tab reaches the checked
// option, arrow keys move and select, like native radios.
const SegmentedControl = <T extends string>({
  'aria-label': ariaLabel,
  className,
  onChange,
  options,
  value,
}: SegmentedControlProps<T>) => {
  const refs = useRef<(HTMLButtonElement | null)[]>([])
  const index = Math.max(
    0,
    options.findIndex((o) => o.value === value),
  )

  const onKeyDown = (e: KeyboardEvent) => {
    const step = { ArrowDown: 1, ArrowLeft: -1, ArrowRight: 1, ArrowUp: -1 }[
      e.key
    ]
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
        'segmented-control d-grid position-relative p-1 rounded-md bg-surface-muted',
        `segmented-control--count-${options.length}`,
        `segmented-control--index-${index}`,
        className,
      )}
      onKeyDown={onKeyDown}
    >
      <span
        aria-hidden
        className='segmented-control__indicator position-absolute rounded-sm bg-surface-default'
      />
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
          className='segmented-control__option position-relative border-0 bg-transparent rounded-sm fw-semibold'
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

export default SegmentedControl
