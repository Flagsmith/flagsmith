import React, { FC, ReactNode } from 'react'
import Icon, { IconName } from './Icon'

type EmptyStateProps = {
  title: string
  description?: string | ReactNode
  icon?: IconName
  iconColour?: string
  docsUrl?: string
  docsLabel?: string
  action?: ReactNode
  className?: string
}

const EmptyState: FC<EmptyStateProps> = ({
  action,
  className,
  description,
  docsLabel = 'View docs',
  docsUrl,
  icon,
  iconColour = '#9DA4AE',
  title,
}) => {
  return (
    <div className={`empty-state ${className || ''}`}>
      {icon && (
        <div className='empty-state__icon'>
          <Icon name={icon} width={40} fill={iconColour} />
        </div>
      )}
      <h5 className='empty-state__title'>{title}</h5>
      {description && (
        <div className='empty-state__description text-muted'>{description}</div>
      )}
      {docsUrl && (
        <a
          href={docsUrl}
          target='_blank'
          rel='noreferrer'
          className='btn btn-link'
        >
          {docsLabel}
        </a>
      )}
      {action}
    </div>
  )
}

export default EmptyState
