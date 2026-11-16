import { ReactNode } from 'react'
import classNames from 'classnames'
import Chip, { ChipSize } from 'components/base/Chip'
import Icon from 'components/icons/Icon'
import './ToggleChip.scss'

export type ToggleChipProps = {
  checked: boolean
  onChange: (checked: boolean) => void
  children: ReactNode
  size?: ChipSize
  // A tag's or environment's own colour; see Chip.
  colour?: string
  disabled?: boolean
  className?: string
}

// A checkbox shown as a chip. Checked chips turn accent and show a tick, so
// the state never relies on colour alone.
const ToggleChip = ({
  checked,
  children,
  className,
  colour,
  disabled,
  onChange,
  size,
}: ToggleChipProps) => (
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
    <Chip colour={colour} selected={checked} size={size}>
      {checked && <Icon name='checkmark' width={16} aria-hidden />}
      {children}
    </Chip>
  </label>
)

export default ToggleChip
