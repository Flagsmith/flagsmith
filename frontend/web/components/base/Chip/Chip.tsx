import React, { KeyboardEvent, ReactNode, Ref } from 'react'
import classNames from 'classnames'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import { getChipColourVars } from './chipColour'
import './Chip.scss'

export type ChipSize = 'default' | 'sm' | 'xs'
export type ChipVariant = 'neutral' | 'accent'

export type ChipProps = {
  children: ReactNode
  variant?: ChipVariant
  size?: ChipSize
  truncate?: boolean
  // 6-digit hex. Replaces the variant.
  colour?: string
  selected?: boolean
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
  colour,
  onClick,
  onKeyDown,
  onRemove,
  ref,
  role,
  selected = false,
  size = 'default',
  tabIndex,
  truncate = false,
  variant = 'neutral',
}: ChipProps) => {
  const interactive = !!onClick || !!role
  const colourVars = colour ? getChipColourVars(colour) : null
  const shownVariant = selected ? 'accent' : variant
  return (
    <span
      ref={ref}
      // Data, not styling: Chip.scss derives the shades from these.
      style={colourVars ?? undefined}
      className={classNames(
        'ds-chip d-inline-flex align-items-center align-middle gap-1 rounded-sm',
        !colourVars && VARIANT_UTILITIES[shownVariant],
        {
          'ds-chip--accent': !colourVars && shownVariant === 'accent',
          'ds-chip--clickable': interactive,
          'ds-chip--selected': !!colourVars && selected,
          'ds-chip--tinted': !!colourVars,
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
