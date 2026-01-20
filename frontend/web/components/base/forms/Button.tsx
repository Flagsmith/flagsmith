import React from 'react'
import cn from 'classnames'
import { ButtonHTMLAttributes, HTMLAttributeAnchorTarget } from 'react'
import Icon, { IconName } from 'components/Icon'
import Constants from 'common/constants'
import Utils, { PaidFeature } from 'common/utils/utils'
import PlanBasedBanner from 'components/PlanBasedAccess'

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
  iconRightColour?: keyof typeof Constants.colours
  iconLeftColour?: keyof typeof Constants.colours
  iconLeft?: IconName
  href?: string
  feature?: PaidFeature
  target?: HTMLAttributeAnchorTarget
  theme?: keyof typeof themeClassNames
  size?: keyof typeof sizeClassNames
  iconSize?: number
}

export const Button = React.forwardRef<
  HTMLButtonElement | HTMLAnchorElement,
  ButtonType
>(
  (
    {
      children,
      className,
      feature,
      href,
      iconLeft,
      iconLeftColour,
      iconRight,
      iconRightColour,
      iconSize = 24,
      onMouseUp,
      size = 'default',
      target,
      theme = 'primary',
      type = 'button',
      ...rest
    },
    ref,
  ) => {
    const hasPlan = feature ? Utils.getPlansPermission(feature) : true
    return href || !hasPlan ? (
      <a
        onClick={
          hasPlan ? (rest.onClick as React.MouseEventHandler) : undefined
        }
        className={cn(className, themeClassNames[theme], sizeClassNames[size])}
        target={hasPlan ? target : '_blank'}
        href={hasPlan ? href : Constants.getUpgradeUrl()}
        rel='noreferrer'
        ref={ref as React.RefObject<HTMLAnchorElement>}
      >
        <div className='d-flex h-100 align-items-center justify-content-center gap-2'>
          {!!iconLeft && !!hasPlan && (
            <Icon
              fill={
                iconLeftColour ? Constants.colours[iconLeftColour] : undefined
              }
              name={iconLeft}
              width={iconSize}
            />
          )}
          {children}
          {!hasPlan && feature && (
            <PlanBasedBanner feature={feature} theme={'badge'} />
          )}
        </div>
        {!!iconRight && (
          <Icon
            fill={
              iconRightColour ? Constants.colours[iconRightColour] : undefined
            }
            className='ml-2'
            name={iconRight}
            width={iconSize}
          />
        )}
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
        {!!iconLeft && (
          <Icon
            fill={
              iconLeftColour ? Constants.colours[iconLeftColour] : undefined
            }
            className='mr-2'
            name={iconLeft}
            width={iconSize}
          />
        )}
        {children}
        {!!iconRight && (
          <Icon
            fill={
              iconRightColour ? Constants.colours[iconRightColour] : undefined
            }
            className='ml-2'
            name={iconRight}
            width={iconSize}
          />
        )}
      </button>
    )
  },
)

Button.displayName = 'Button'
export default Button
