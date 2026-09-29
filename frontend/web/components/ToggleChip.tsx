import React, { FC, ReactNode } from 'react'
import cx from 'classnames'
import Icon from './icons/Icon'
import Chip from './base/Chip'
import './ToggleChip.scss'

type ToggleChipProps = {
  active?: boolean
  onClick?: () => void
  className?: string
  children?: ReactNode
  /** Names a chip whose content cannot, such as a bare colour swatch. */
  label?: string
}

const ToggleChip: FC<ToggleChipProps> = ({
  active,
  children,
  className,
  label,
  onClick,
}) => (
  <Chip
    aria-label={label}
    // Only where it toggles: on a chip that does nothing, a pressed state
    // would announce an interaction that is not there.
    aria-pressed={onClick ? !!active : undefined}
    className={cx('no-wrap mr-1 mt-0', className)}
    onClick={onClick}
    size='xs'
    variant='none'
  >
    {/* Without a label this is a bare swatch, e.g. the tag colour picker, where
        the box would be noise: the tick alone marks the selection. */}
    <span
      className={cx('d-inline-flex align-items-center justify-content-center', {
        'toggle-chip__check flex-shrink-0 rounded-xs': !!children,
        'toggle-chip__check--active': active && !!children,
      })}
    >
      {active && <Icon name='checkmark' width={14} />}
    </span>
    {children}
  </Chip>
)

export default ToggleChip
