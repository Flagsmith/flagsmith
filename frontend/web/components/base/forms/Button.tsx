import React from 'react'
import cn from 'classnames'
import { ButtonHTMLAttributes, HTMLAttributeAnchorTarget } from 'react'
import Icon, { IconName } from 'components/icons/Icon'

const iconColours = {
  primary: '#6837fc',
  white: '#ffffff',
} as const

export type IconColour = keyof typeof iconColours

export const themeClassNames = {
  danger: 'btn btn-danger',
  icon: 'btn-icon',
  outline: 'btn--outline',
  primary: 'btn-primary',
  project: 'btn-project',
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
  iconRight?: IconName
  iconRightColour?: IconColour
  iconLeftColour?: IconColour
  iconLeft?: IconName
  href?: string
  target?: HTMLAttributeAnchorTarget
  theme?: keyof typeof themeClassNames
  size?: keyof typeof sizeClassNames
  iconSize?: number
  isLoading?: boolean
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
      iconLeft,
      iconLeftColour,
      iconRight,
      iconRightColour,
      iconSize = 24,
      isLoading = false,
      loadingLabel = 'Saving...',
      onMouseUp,
      size = 'default',
      target,
      theme = 'primary',
      type = 'button',
      ...rest
    },
    ref,
  ) => {
    const buttonContent = isLoading ? (
      <div className='d-flex align-items-center justify-content-center gap-2'>
        <Loader width='15px' height='15px' />
        <span>{loadingLabel}</span>
      </div>
    ) : (
      <>
        {!!iconLeft && (
          <Icon
            fill={iconLeftColour ? iconColours[iconLeftColour] : undefined}
            className='mr-2'
            name={iconLeft}
            width={iconSize}
          />
        )}
        {children}
        {!!iconRight && (
          <Icon
            fill={iconRightColour ? iconColours[iconRightColour] : undefined}
            className='ml-2'
            name={iconRight}
            width={iconSize}
          />
        )}
      </>
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
        <div className='d-flex h-100 align-items-center justify-content-center gap-2'>
          {!!iconLeft && (
            <Icon
              fill={iconLeftColour ? iconColours[iconLeftColour] : undefined}
              name={iconLeft}
              width={iconSize}
            />
          )}
          {children}
        </div>
        {!!iconRight && (
          <Icon
            fill={iconRightColour ? iconColours[iconRightColour] : undefined}
            className='ml-2'
            name={iconRight}
            width={iconSize}
          />
        )}
      </a>
    ) : (
      <button
        {...rest}
        aria-busy={isLoading}
        aria-live='polite'
        disabled={isLoading || disabled}
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
        {buttonContent}
      </button>
    )
  },
)

Button.displayName = 'Button'
export default Button