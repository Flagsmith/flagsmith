import { ReactNode } from 'react'
import classNames from 'classnames'
import './Radio.scss'

export type RadioIndicatorPosition = 'start' | 'end'

export type RadioProps<T extends string> = {
  // Shared by the radios of one group, so arrow keys move between them.
  name: string
  value: T
  checked: boolean
  // Fires when this option is chosen; a radio is never unselected by a click.
  onChange: (value: T) => void
  children: ReactNode
  // 'end' puts the dot after the label, for a full-width row.
  indicatorPosition?: RadioIndicatorPosition
  disabled?: boolean
  className?: string
}

const Radio = <T extends string>({
  checked,
  children,
  className,
  disabled,
  indicatorPosition = 'start',
  name,
  onChange,
  value,
}: RadioProps<T>) => {
  const dot = <span aria-hidden className='ds-radio__dot flex-shrink-0' />
  return (
    <label
      className={classNames(
        'ds-radio d-flex align-items-center gap-2 mb-0',
        disabled ? 'ds-radio--disabled' : 'cursor-pointer',
        className,
      )}
    >
      <input
        type='radio'
        className='visually-hidden'
        name={name}
        value={value}
        checked={checked}
        disabled={disabled}
        onChange={() => onChange(value)}
      />
      {indicatorPosition === 'start' && dot}
      {children}
      {indicatorPosition === 'end' && dot}
    </label>
  )
}

export default Radio
