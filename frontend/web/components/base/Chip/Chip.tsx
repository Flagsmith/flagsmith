import React, { KeyboardEvent, ReactNode, Ref } from 'react'
import classNames from 'classnames'
import Icon from 'components/icons/Icon'
import ColorSwatch from 'components/ColorSwatch'
import { colorIconSecondary } from 'common/theme/tokens'
import './Chip.scss'

export type ChipSize = 'default' | 'sm' | 'xs'
export type ChipVariant = 'neutral' | 'accent'

export type ChipProps = {
  children: ReactNode
  variant?: ChipVariant
  // A colour the chip carries as a dot in front of its label, rather than as
  // a fill. Any CSS colour; see dotColour for moving an arbitrary one to
  // where it reads on the chip.
  dot?: string
  // Chosen. Draws the ring, and announces itself as pressed where the chip is
  // a button, so the two cannot disagree. A caller driving a keyboard group
  // sets aria-checked instead and keeps the ring.
  selected?: boolean
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
  'aria-label'?: string
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
  'aria-label': ariaLabel,
  children,
  className,
  dot,
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
  const chosen = selected || ariaChecked === true
  return (
    <span
      ref={ref}
      className={classNames(
        'ds-chip d-inline-flex align-items-center align-middle gap-1 rounded-sm',
        VARIANT_UTILITIES[variant],
        {
          'ds-chip--accent': variant === 'accent',
          'ds-chip--clickable': interactive,
          'ds-chip--selected': chosen,
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
      aria-label={ariaLabel}
      aria-pressed={
        // aria-pressed needs the button role, which only onClick gives it.
        onClick && !role ? selected : undefined
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
      {dot && <ColorSwatch color={dot} shape='circle' size='sm' />}
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
