import React, { FC, ReactNode } from 'react'
import Icon from 'components/Icon'

interface EmptyStateProps {
  title: string
  description: string
  icon?: string
  iconColor?: string
  actions?: ReactNode
  className?: string
  marginTop?: string
}

const EmptyState: FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  iconColor,
  actions,
  className = '',
  marginTop = '8rem'
}) => {
  return (
    <div 
      className={`text-center empty-state ${className}`}
      style={{ '--empty-state-margin-top': marginTop } as React.CSSProperties}
    >
      {icon && (
        <div className='mb-3'>
          <Icon name={icon} width={36} className={iconColor ? '' : 'text-primary'} fill={iconColor} />
        </div>
      )}
      <h4 className='mb-2 empty-state-title'>
        {title}
      </h4>
      <p className='text-muted mb-4 empty-state-description'>
        {description}
      </p>
      {actions && (
        <div className='d-flex align-items-center justify-content-center gap-3'>
          {actions}
        </div>
      )}
    </div>
  )
}

export default EmptyState
export type { EmptyStateProps }
