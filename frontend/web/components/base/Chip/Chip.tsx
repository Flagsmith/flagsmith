import React, { KeyboardEvent, ReactNode, Ref } from 'react'
import classNames from 'classnames'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import type { ContentColour } from 'common/theme/tokens'
import { chipDotClass, chipVariantClass, ChipVariant } from './chipColour'
import './Chip.scss'

export type ChipSize = 'md' | 'sm' | 'xs'

export type ChipProps = {
  variant?: ChipVariant
  // A hue the chip carries as a dot rather than as a fill, so the surface and
  // the label stay the neutral ones in both themes.
  dot?: ContentColour
  // Chosen. Draws the ring, and announces itself as pressed where the chip is
  // a button, so the two cannot disagree. A caller driving a keyboard group
  // sets aria-checked instead and keeps the ring.
  selected?: boolean
  children: ReactNode
  size?: ChipSize
  truncate?: boolean
  onRemove?: () => void
  onClick?: () => void
  className?: string
  // Opt into membership of a keyboard group (e.g. a radiogroup): supply the
  // role, roving tabIndex, checked state, key handler and ref. These override
  // the button semantics onClick applies by default, so the group owner can
  // drive arrow-key navigation.
  role?: 'button' | 'radio'
  tabIndex?: number
  'aria-checked'?: boolean
  'aria-pressed'?: boolean
  'aria-expanded'?: boolean
  'aria-label'?: string
  onKeyDown?: (e: KeyboardEvent) => void
  ref?: Ref<HTMLSpanElement>
}

const Chip = ({
  'aria-checked': ariaChecked,
  'aria-expanded': ariaExpanded,
  'aria-label': ariaLabel,
  'aria-pressed': ariaPressed,
  children,
  className,
  dot,
  onClick,
  onKeyDown,
  onRemove,
  ref,
  role,
  selected,
  size = 'md',
  tabIndex,
  truncate = false,
  variant,
}: ChipProps) => {
  const interactive = !!onClick || !!role
  const chosen = selected || ariaPressed === true || ariaChecked === true
  return (
    <span
      ref={ref}
      className={classNames(
        'ds-chip d-inline-flex align-items-center align-middle gap-1 rounded-md',
        chipVariantClass(variant),
        {
          'ds-chip--accent': variant === 'accent',
          'ds-chip--clickable': interactive,
          'ds-chip--selected': chosen,
          [`ds-chip--${size}`]: size !== 'md',
          'ds-chip--truncate': truncate,
        },
        className,
      )}
      onClick={onClick}
      role={role ?? (onClick ? 'button' : undefined)}
      tabIndex={interactive ? tabIndex ?? 0 : undefined}
      aria-checked={ariaChecked}
      aria-expanded={ariaExpanded}
      aria-pressed={
        // aria-pressed needs the button role, which only onClick gives it.
        ariaPressed ?? (onClick && !role ? selected : undefined)
      }
      aria-label={ariaLabel}
      onKeyDown={
        onKeyDown ??
        (onClick
          ? (e: KeyboardEvent) => {
              // Activate like a button: Enter/Space fire onClick (preventDefault
              // stops Space scrolling the page).
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onClick()
              }
            }
          : undefined)
      }
    >
      {dot && (
        <span
          aria-hidden='true'
          className={classNames(
            'ds-chip__dot rounded-circle',
            chipDotClass(dot),
          )}
        />
      )}
      {truncate ? <span className='ds-chip__label'>{children}</span> : children}
      {onRemove && (
        <button
          type='button'
          className='ds-chip__remove d-inline-flex align-items-center'
          aria-label='Remove'
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
        >
          <Icon name='close' width={12} fill={colorIconSecondary} />
        </button>
      )}
    </span>
  )
}

export default Chip
