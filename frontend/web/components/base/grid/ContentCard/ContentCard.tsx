import { FC, ReactNode } from 'react'
import cn from 'classnames'
import './ContentCard.scss'

type ContentCardProps = {
  title?: string
  description?: ReactNode
  action?: ReactNode
  className?: string
  compact?: boolean
  children: ReactNode
}

const ContentCard: FC<ContentCardProps> = ({
  action,
  children,
  className,
  compact,
  description,
  title,
}) => {
  return (
    <div
      className={cn(
        'content-card',
        compact && 'content-card--compact',
        className,
      )}
    >
      {(title || action || description) && (
        <div className='content-card__heading'>
          {(title || action) && (
            <div className='content-card__header'>
              {title && <span className='content-card__title'>{title}</span>}
              {action}
            </div>
          )}
          {description && (
            <p className='content-card__description'>{description}</p>
          )}
        </div>
      )}
      {children}
    </div>
  )
}

export default ContentCard
