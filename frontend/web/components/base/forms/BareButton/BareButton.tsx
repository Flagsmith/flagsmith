import React, { ButtonHTMLAttributes } from 'react'
import cn from 'classnames'
import './BareButton.scss'

export type BareButtonProps = ButtonHTMLAttributes<HTMLButtonElement>

/**
 * A semantically correct `<button>` with all browser defaults reset.
 *
 * Use this instead of `<div role="button">` whenever you need a clickable
 * surface that doesn't look like a traditional button (stepper steps,
 * selectable cards, list rows, chip-delete icons, etc.).
 *
 * It gives you focus management, disabled semantics, keyboard handling and
 * screen-reader role for free — without manual `tabIndex`, `onKeyDown` or
 * `role` attributes.
 */
export const BareButton = React.forwardRef<HTMLButtonElement, BareButtonProps>(
  ({ children, className, type = 'button', ...rest }, ref) => {
    return (
      <button
        {...rest}
        type={type}
        className={cn('bare-btn', className)}
        ref={ref}
      >
        {children}
      </button>
    )
  },
)

BareButton.displayName = 'BareButton'
export default BareButton
