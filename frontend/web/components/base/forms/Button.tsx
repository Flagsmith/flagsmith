import cn from 'classnames'
import { ButtonHTMLAttributes, FC, HTMLAttributeAnchorTarget } from 'react'
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
  tertiary: 'btn-tertiary',
  text: 'btn-link',
}

export const sizeClassNames = {
  default: '',
  large: 'btn-lg',
  small: 'btn-sm',
  xSmall: 'btn-xsm',
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
}

export const Button: FC<ButtonType> = ({
  children,
  className,
  feature,
  href,
  iconLeft,
  iconLeftColour,
  iconRight,
  iconRightColour,
  onMouseUp,
  size = 'default',
  target,
  theme = 'primary',
  type = 'button',
  ...rest
}) => {
  const hasPlan = feature ? Utils.getPlansPermission(feature) : true
  return href || !hasPlan ? (
    <a
      onClick={rest.onClick}
      className={cn(className, themeClassNames[theme], sizeClassNames[size])}
      target={target}
      href={hasPlan ? href : Constants.getUpgradeUrl()}
      rel='noreferrer'
    >
      {!!iconLeft && (
        <Icon
          fill={iconLeftColour ? Constants.colours[iconLeftColour] : undefined}
          className='me-2'
          name={iconLeft}
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
    >
      {!!iconLeft && (
        <Icon
          fill={iconLeftColour ? Constants.colours[iconLeftColour] : undefined}
          className='mr-2'
          name={iconLeft}
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
        />
      )}
    </button>
  )
}

Button.displayName = 'Button'
export default Button
