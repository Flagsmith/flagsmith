import React, { KeyboardEvent, ReactNode, Ref } from 'react'
import classNames from 'classnames'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import './Chip.scss'

export type ChipSize = 'default' | 'sm' | 'xs'
export type ChipVariant =
  | 'neutral'
  | 'accent'
  // The caller supplies the colour through className. Used by tags, whose
  // colour is a user's decorative choice rather than a semantic role.
  | 'none'

export type ChipProps = {
  children: ReactNode
  variant?: ChipVariant
  size?: ChipSize
  truncate?: boolean
  /** Rings the chip when chosen. Lists mark rows instead: see TagRow. */
  selected?: boolean
  onRemove?: () => void
  onClick?: () => void
  className?: string
  // Membership of a caller-driven keyboard group, overriding the default
  // button semantics. See SdkPicker.
  role?: 'button' | 'radio'
  tabIndex?: number
  'aria-checked'?: boolean
  'aria-expanded'?: boolean
  // For a chip whose content cannot name it, such as a bare colour swatch.
  'aria-label'?: string
  // Toggle state, for a chip that is on or off rather than navigating.
  'aria-pressed'?: boolean
  onKeyDown?: (e: KeyboardEvent) => void
  ref?: Ref<HTMLSpanElement>
}

// bg + text come from token utilities; the variant border lives in Chip.scss.
const VARIANT_UTILITIES: Record<ChipVariant, string> = {
  accent: 'bg-surface-action-subtle text-action',
  neutral: 'bg-surface-subtle text-default',
  none: '',
}

// `ds-chip` rather than the legacy `.chip`, which ~35 components still use.
const Chip = ({
  'aria-checked': ariaChecked,
  'aria-expanded': ariaExpanded,
  'aria-label': ariaLabel,
  'aria-pressed': ariaPressed,
  children,
  className,
  onClick,
  onKeyDown,
  onRemove,
  ref,
  role,
  selected,
  size = 'default',
  tabIndex,
  truncate = false,
  variant = 'neutral',
}: ChipProps) => {
  const interactive = !!onClick || !!role
  return (
    <span
      ref={ref}
      className={classNames(
        // 6px radius is fixed by the design system's tags frame.
        'ds-chip d-inline-flex align-items-center align-middle gap-2 rounded-md',
        VARIANT_UTILITIES[variant],
        {
          'ds-chip--accent': variant === 'accent',
          'ds-chip--clickable': interactive,
          'ds-chip--ring': selected,
          'ds-chip--truncate': truncate,
          [`ds-chip--${size}`]: size !== 'default',
        },
        className,
      )}
      onClick={onClick}
      role={role ?? (onClick ? 'button' : undefined)}
      tabIndex={interactive ? tabIndex ?? 0 : undefined}
      // `selected` reports through whichever the role supports: a button is
      // pressed, a radio or checkbox is checked.
      aria-checked={
        ariaChecked ?? (role && role !== 'button' ? selected : undefined)
      }
      aria-expanded={ariaExpanded}
      aria-label={ariaLabel}
      aria-pressed={
        ariaPressed ?? (role && role !== 'button' ? undefined : selected)
      }
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
