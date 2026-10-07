import React, { KeyboardEvent, ReactNode, Ref } from 'react'
import classNames from 'classnames'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import type { ContentColour } from 'common/theme/tokens'
import { chipColourClass, chipVariantClass, ChipVariant } from './chipColour'
import './Chip.scss'

export type ChipSize = 'md' | 'sm' | 'xs'

type ChipColour =
  | { variant?: ChipVariant; colour?: never }
  | { variant?: never; colour: ContentColour }

export type ChipProps = ChipColour & {
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
  colour,
  onClick,
  onKeyDown,
  onRemove,
  ref,
  role,
  size = 'md',
  tabIndex,
  truncate = false,
  variant,
}: ChipProps) => {
  const interactive = !!onClick || !!role
  return (
    <span
      ref={ref}
      className={classNames(
        'ds-chip d-inline-flex align-items-center align-middle gap-1 rounded-md',
        colour ? chipColourClass(colour) : chipVariantClass(variant),
        {
          'ds-chip--accent': variant === 'accent',
          'ds-chip--clickable': interactive,
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
      aria-pressed={ariaPressed}
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
