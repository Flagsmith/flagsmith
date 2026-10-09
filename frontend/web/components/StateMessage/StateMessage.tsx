import { FC, ReactNode } from 'react'
import cn from 'classnames'
import { colorIconSecondary } from 'common/theme/tokens'
import Icon, { IconName } from 'components/icons/Icon'
import './StateMessage.scss'

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
  <div className={cn('state-message text-center', className)} role={role}>
    {icon && (
      <div className='mb-3' aria-hidden>
        <Icon name={icon} width={40} fill={iconColour} />
      </div>
    )}
    <h5 className='mb-2'>{title}</h5>
    {description && (
      <div className='state-message__description mx-auto mb-3 text-muted'>
        {description}
      </div>
    )}
    {action}
  </div>
)

export default StateMessage
