import React, { KeyboardEvent, ReactNode, Ref } from 'react'
import classNames from 'classnames'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import './Chip.scss'

export type ChipSize = 'default' | 'sm' | 'xs'
export type ChipVariant =
  | 'neutral'
  | 'accent'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'muted'
  | 'solid'
  // Colour comes from className. Used by tags.
  | 'none'

export type ChipProps = {
  children: ReactNode
  variant?: ChipVariant
  size?: ChipSize
  truncate?: boolean
  /** Rings the chip when chosen, fades it when not. Lists mark rows instead: see TagRow. */
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
  onKeyDown?: (e: KeyboardEvent) => void
  ref?: Ref<HTMLSpanElement>
}

// bg + text come from token utilities; the variant border lives in Chip.scss.
const VARIANT_UTILITIES: Record<ChipVariant, string> = {
  accent: 'bg-surface-action-subtle text-action',

  danger: 'bg-surface-danger text-danger',

  info: 'bg-surface-info text-info',

  muted: 'bg-surface-muted text-secondary',

  neutral: 'bg-surface-subtle text-default',
  none: '',
  // text-white, not a token: there is no inverse-text token yet. 5.93:1, AA.
  solid: 'bg-surface-action text-white',
  success: 'bg-surface-success text-success',
  warning: 'bg-surface-warning text-warning',
}

// `ds-chip` rather than the legacy `.chip`, which ~35 components still use.
const Chip = ({
  'aria-checked': ariaChecked,
  'aria-expanded': ariaExpanded,
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
        `ds-chip--${variant}`,
        {
          'ds-chip--clickable': interactive,
          'ds-chip--ring': selected,
          'ds-chip--truncate': truncate,
          [`ds-chip--${size}`]: size !== 'default',
          'ds-chip--unselected': selected === false,
        },
        className,
      )}
      onClick={onClick}
      role={role ?? (onClick ? 'button' : undefined)}
      tabIndex={interactive ? tabIndex ?? 0 : undefined}
      aria-checked={ariaChecked ?? selected}
      aria-expanded={ariaExpanded}
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
