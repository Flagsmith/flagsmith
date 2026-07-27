import React from 'react'
import cn from 'classnames'
import { ButtonHTMLAttributes, HTMLAttributeAnchorTarget } from 'react'
import Loader from 'components/Loader'

export const themeClassNames = {
  danger: 'btn-danger',
  icon: 'btn-icon',
  outline: 'btn--outline',
  primary: 'btn-primary',
  project: 'btn-project',
  secondary: 'btn-secondary',
  success: 'btn-success',
  tertiary: 'btn-tertiary',
  text: 'btn-link',
}

export const sizeClassNames = {
  default: '',
  large: 'btn-lg',
  small: 'btn-sm',
  xSmall: 'btn-xsm',
  xxSmall: 'btn-xxsm',
}

export type ButtonType = ButtonHTMLAttributes<HTMLButtonElement> & {
  href?: string
  target?: HTMLAttributeAnchorTarget
  theme?: keyof typeof themeClassNames
  size?: keyof typeof sizeClassNames
  isLoading?: boolean
  // Replaces children while loading (e.g. 'Saving…'). Omit to keep the
  // label beside the spinner, the existing behaviour at adopted sites.
  loadingLabel?: string
}

export const Button = React.forwardRef<
  HTMLButtonElement | HTMLAnchorElement,
  ButtonType
>(
  (
    {
      children,
      className,
      disabled,
      href,
      isLoading = false,
      loadingLabel,
      onMouseUp,
      size = 'default',
      target,
      theme = 'primary',
      type = 'button',
      ...rest
    },
    ref,
  ) => {
    const classes = cn(
      'btn',
      className,
      themeClassNames[theme],
      sizeClassNames[size],
      isLoading && 'd-inline-flex align-items-center gap-2',
    )
    const content = (
      <>
        {isLoading && <Loader width='15px' height='15px' />}
        {isLoading && loadingLabel ? loadingLabel : children}
      </>
    )
    return href ? (
      // Anchors cannot be disabled, so a loading link gets Bootstrap's
      // .disabled (pointer-events: none) plus a click guard for keyboard
      // activation, and the same aria state as the button variant.
      <a
        onClick={
          isLoading
            ? (e) => e.preventDefault()
            : (rest.onClick as React.MouseEventHandler)
        }
        className={cn(classes, isLoading && 'disabled')}
        target={target}
        href={href}
        rel='noreferrer'
        aria-disabled={isLoading || undefined}
        aria-busy={isLoading || undefined}
        aria-live='polite'
        ref={ref as React.RefObject<HTMLAnchorElement>}
      >
        {content}
      </a>
    ) : (
      <button
        {...rest}
        disabled={disabled || isLoading}
        type={type}
        onMouseUp={onMouseUp}
        className={classes}
        aria-busy={isLoading || undefined}
        aria-live='polite'
        ref={ref as React.RefObject<HTMLButtonElement>}
      >
        {content}
      </button>
    )
  },
)

Button.displayName = 'Button'
export default Button
