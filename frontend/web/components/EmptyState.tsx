import React, { FC, ReactNode } from 'react'
import { colorIconDanger, colorIconSecondary } from 'common/theme/tokens'
import Icon, { IconName } from './icons/Icon'
import Button from './base/forms/Button'

export type EmptyStateStatus = 'empty' | 'error'

type EmptyStateProps = {
  title: string
  description?: string | ReactNode
  // 'error' is for content that failed to load: pair it with a retry action
  status?: EmptyStateStatus
  icon?: IconName
  iconColour?: string
  docsUrl?: string
  docsLabel?: string
  action?: ReactNode
  // Renders a Try again button, and a matching description unless one is given
  onRetry?: () => void
  className?: string
}

const EmptyState: FC<EmptyStateProps> = ({
  action,
  className,
  description,
  docsLabel = 'View docs',
  docsUrl,
  icon,
  iconColour,
  onRetry,
  status = 'empty',
  title,
}) => {
  const isError = status === 'error'
  const iconName = icon ?? (isError ? 'warning' : undefined)
  const text =
    description ?? (onRetry ? 'Try again in a few moments.' : undefined)
  return (
    <div
      // A failed load is announced as soon as it lands
      role={isError ? 'alert' : undefined}
      className={`empty-state ${className || ''}`}
    >
      {iconName && (
        <div className='empty-state__icon'>
          <Icon
            name={iconName}
            width={40}
            fill={
              iconColour ?? (isError ? colorIconDanger : colorIconSecondary)
            }
          />
        </div>
      )}
      <h5 className='empty-state__title'>{title}</h5>
      {text && (
        <div className='empty-state__description text-muted'>{text}</div>
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
      {onRetry && (
        <Button theme='outline' size='small' onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  )
}

export default EmptyState
