import { ReactNode } from 'react'
import classNames from 'classnames'
import Chip, { ChipSize, ChipVariantProps } from 'components/base/Chip'
import Icon from 'components/icons/Icon'
import './ToggleChip.scss'

export type ToggleChipProps = {
  checked: boolean
  onChange: (checked: boolean) => void
  children: ReactNode
  size?: ChipSize
  colour?: string
  disabled?: boolean
  className?: string
}

const ToggleChip = ({
  checked,
  children,
  className,
  colour,
  disabled,
  onChange,
  size,
}: ToggleChipProps) => {
  const chipVariant: ChipVariantProps = colour
    ? { colour, variant: 'tinted' }
    : { variant: checked ? 'accent' : 'neutral' }
  return (
    <label
      className={classNames(
        'ds-toggle-chip d-inline-flex mb-0',
        disabled ? 'ds-toggle-chip--disabled' : 'cursor-pointer',
        className,
      )}
    >
      <input
        type='checkbox'
        className='visually-hidden'
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
      />
      <Chip {...chipVariant} size={size}>
        {checked && <Icon name='checkmark' width={16} aria-hidden />}
        {children}
      </Chip>
    </label>
  )
}

export default ToggleChip
