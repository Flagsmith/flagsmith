import cn from 'classnames'
import { ButtonHTMLAttributes, FC } from 'react'
import Icon, { IconName } from 'components/Icon'

export const themeClassNames = {
  danger: 'btn btn-danger',
  outline: 'btn btn--outline',
  primary: 'btn-primary',
  project: 'btn-project',
  secondary: 'btn-secondary',
  tertiary: 'btn-tertiary',
  text: 'btn-link',
}

export const sizeClassNames = {
  default: '',
  large: 'btn-lg',
  small: 'btn-sm',
}

export type ButtonType = ButtonHTMLAttributes<HTMLButtonElement> & {
  iconRight?: IconName
  iconLeft?: IconName
  theme?: keyof typeof themeClassNames
  size?: keyof typeof sizeClassNames
}

export const Button: FC<ButtonType> = ({
  children,
  className,
  iconLeft,
  iconRight,
  onMouseUp,
  size = 'default',
  theme = 'primary',
  type = 'submit',
  ...rest
}) => {
  return (
    <button
      type={type}
      {...rest}
      onMouseUp={onMouseUp}
      className={cn(
        { btn: true },
        className,
        themeClassNames[theme],
        sizeClassNames[size],
      )}
    >
      {!!iconLeft && <Icon className='mr-1' name={iconLeft} />}
      {children}
      {!!iconRight && <Icon className='ml-2' name={iconRight} />}
    </button>
  )
}

Button.displayName = 'Button'
export default Button
