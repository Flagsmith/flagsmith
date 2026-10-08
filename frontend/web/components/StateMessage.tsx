import { FC, ReactNode } from 'react'
import { colorIconSecondary } from 'common/theme/tokens'
import Icon, { IconName } from './icons/Icon'

export type StateMessageProps = {
  title: string
  description?: ReactNode
  icon?: IconName
  iconColour?: string
  action?: ReactNode
  className?: string
  role?: 'alert' | 'status'
}

const StateMessage: FC<StateMessageProps> = ({
  action,
  className,
  description,
  icon,
  iconColour = colorIconSecondary,
  role,
  title,
}) => (
  <div className={`state-message ${className || ''}`} role={role}>
    {icon && (
      <div className='state-message__icon'>
        <Icon name={icon} width={40} fill={iconColour} />
      </div>
    )}
    <h5 className='state-message__title'>{title}</h5>
    {description && (
      <div className='state-message__description text-muted'>{description}</div>
    )}
    {action}
  </div>
)

export default StateMessage
