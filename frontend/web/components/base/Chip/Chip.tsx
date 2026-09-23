import React, { KeyboardEvent, ReactNode, Ref } from 'react'
import classNames from 'classnames'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import './Chip.scss'

export type ChipSize = 'default' | 'sm' | 'xs'
export type ChipVariant = 'neutral' | 'accent'

export type ChipProps = {
  children: ReactNode
  variant?: ChipVariant
  size?: ChipSize
  truncate?: boolean
  onRemove?: () => void
  onClick?: () => void
  className?: string
  // Opt into membership of a keyboard group (e.g. a radiogroup): supply the
  // role, roving tabIndex, checked state, key handler and ref. These override
  // the button semantics onClick applies by default, so the group owner can
  // drive arrow-key navigation. See SdkPicker.
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
  neutral: 'bg-surface-subtle text-default',
}

// Token-based chip primitive. Uses `ds-chip` rather than the legacy `.chip`
// (old SCSS vars + a manual `.dark {}` block, ~35 usages) so the two coexist
// until those migrate under #6606. Clickable on its own (role=button), or a
// member of a caller-driven keyboard group via the role/tabIndex/onKeyDown/ref
// props. Count badges are out of scope.
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
        'ds-chip d-inline-flex align-items-center align-middle gap-1 rounded-sm',
        VARIANT_UTILITIES[variant],
        {
          'ds-chip--accent': variant === 'accent',
          'ds-chip--clickable': interactive,
          [`ds-chip--${size}`]: size !== 'default',
          'ds-chip--truncate': truncate,
        },
        className,
      )}
      onClick={onClick}
      role={role ?? (onClick ? 'button' : undefined)}
      tabIndex={interactive ? tabIndex ?? 0 : undefined}
      aria-checked={ariaChecked}
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
