import { FC, ReactNode } from 'react'
import cn from 'classnames'
import BareButton, { BareButtonProps } from 'components/base/forms/BareButton'
import './IconButton.scss'

export type IconButtonVariant =
  | 'primary'
  | 'secondary'
  | 'outline'
  | 'destructive'
  | 'ghost'

export type IconButtonSize = 'small' | 'medium' | 'large'

// A separate component from Button, which stays text-only. Nothing is migrated
// onto this yet.
export type IconButtonProps = BareButtonProps & {
  // There is no label to read, so the accessible name is required rather than
  // something a caller can forget.
  'aria-label': string
  variant?: IconButtonVariant
  size?: IconButtonSize
  children: ReactNode
}

const IconButton: FC<IconButtonProps> = ({
  children,
  className,
  size = 'large',
  variant = 'primary',
  ...rest
}) => (
  <BareButton
    {...rest}
    className={cn(
      'ds-icon-button',
      `ds-icon-button--${variant}`,
      `ds-icon-button--${size}`,
      className,
    )}
  >
    <span className='ds-icon-button__icon' aria-hidden>
      {children}
    </span>
  </BareButton>
)

export default IconButton
