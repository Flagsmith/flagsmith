import React from 'react'
import cn from 'classnames'
import { ButtonHTMLAttributes, HTMLAttributeAnchorTarget } from 'react'

export const themeClassNames = {
  danger: 'btn-danger',
  icon: 'btn-icon',
  outline: 'btn--outline',
  primary: 'btn-primary',
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
}

export const Button = React.forwardRef<
  HTMLButtonElement | HTMLAnchorElement,
  ButtonType
>(
  (
    {
      children,
      className,
      href,
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
        type={type}
        onMouseUp={onMouseUp}
        className={classes}
        ref={ref as React.RefObject<HTMLButtonElement>}
      >
        {children}
      </button>
    )
  },
)

Button.displayName = 'Button'
export default Button
