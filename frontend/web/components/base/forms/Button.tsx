import React from 'react'
import cn from 'classnames'
import { ButtonHTMLAttributes, HTMLAttributeAnchorTarget } from 'react'

export const themeClassNames = {
  danger: 'btn btn-danger',
  icon: 'btn-icon',
  outline: 'btn--outline',
  primary: 'btn-primary',
  secondary: 'btn btn-secondary',
  success: 'btn btn-success',
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
    const content =
      React.Children.count(children) > 1 ? (
        <span className='d-flex h-100 align-items-center justify-content-center gap-2'>
          {children}
        </span>
      ) : (
        children
      )
    return href ? (
      <a
        onClick={rest.onClick as React.MouseEventHandler}
        className={cn(className, themeClassNames[theme], sizeClassNames[size])}
        target={target}
        href={href}
        rel='noreferrer'
        ref={ref as React.RefObject<HTMLAnchorElement>}
      >
        {content}
      </a>
    ) : (
      <button
        {...rest}
        type={type}
        onMouseUp={onMouseUp}
        className={cn(
          { btn: true },
          className,
          themeClassNames[theme],
          sizeClassNames[size],
        )}
        ref={ref as React.RefObject<HTMLButtonElement>}
      >
        {content}
      </button>
    )
  },
)

Button.displayName = 'Button'
export default Button
