import React, { ButtonHTMLAttributes, forwardRef } from 'react'
import './BareButton.scss'

type BareButtonProps = ButtonHTMLAttributes<HTMLButtonElement>

/**
 * A button with no default chrome — just a clickable, keyboard-accessible
 * surface. Use when you need a `<button>` for accessibility (keyboard
 * activation, focus, screen-reader semantics) but the visual design is
 * a styled custom shape — e.g. card rows, custom radios, icon-only
 * triggers — that shouldn't inherit the project's `.btn` styling.
 *
 * Defaults `type='button'` so it never accidentally submits a parent
 * form. Provides a `bare-button` reset class plus a default
 * `:focus-visible` outline so keyboard users see where they are.
 */
const BareButton = forwardRef<HTMLButtonElement, BareButtonProps>(
  ({ className, type = 'button', ...rest }, ref) => (
    <button
      ref={ref}
      type={type}
      className={`bare-button ${className ?? ''}`.trim()}
      {...rest}
    />
  ),
)

BareButton.displayName = 'BareButton'

export default BareButton
