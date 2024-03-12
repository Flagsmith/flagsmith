import cn from 'classnames'
import { ButtonHTMLAttributes, FC, HTMLAttributeAnchorTarget } from 'react'
import Icon, { IconName } from 'components/Icon'
import Constants from 'common/constants'

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
  target?: HTMLAttributeAnchorTarget
  theme?: keyof typeof themeClassNames
  size?: keyof typeof sizeClassNames
}

export const Button: FC<ButtonType> = ({
  children,
  className,
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
  return href ? (
    <a
      className={cn(className, themeClassNames[theme], sizeClassNames[size])}
      target={target}
      href={href}
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
