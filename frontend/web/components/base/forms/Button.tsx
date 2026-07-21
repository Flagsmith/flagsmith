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
    return href ? (
      <a
        onClick={rest.onClick as React.MouseEventHandler}
        className={classes}
        target={target}
        href={href}
        rel='noreferrer'
        ref={ref as React.RefObject<HTMLAnchorElement>}
      >
        {children}
      </a>
    ) : (
      <button
        {...rest}
        disabled={disabled || isLoading}
        type={type}
        onMouseUp={onMouseUp}
        className={classes}
        ref={ref as React.RefObject<HTMLButtonElement>}
      >
        {isLoading && <Loader width='15px' height='15px' />}
        {children}
      </button>
    )
  },
)

Button.displayName = 'Button'
export default Button
