import { ReactNode } from 'react'
import classNames from 'classnames'
import Chip, { ChipSize } from 'components/base/Chip'
import Icon from 'components/icons/Icon'
import { colorIconAction } from 'common/theme/tokens'
import './ToggleChip.scss'

export type ToggleChipProps = {
  checked: boolean
  onChange: (checked: boolean) => void
  children: ReactNode
  size?: ChipSize
  disabled?: boolean
  className?: string
}

// A checkbox shown as a chip. Checked chips turn accent and show a tick, so
// the state never relies on colour alone.
const ToggleChip = ({
  checked,
  children,
  className,
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
    <Chip variant={checked ? 'accent' : 'neutral'} size={size}>
      {checked && (
        <Icon name='checkmark' width={16} fill={colorIconAction} aria-hidden />
      )}
      {children}
    </Chip>
  </label>
)

export default ToggleChip
