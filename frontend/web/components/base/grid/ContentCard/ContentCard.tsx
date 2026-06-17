import { FC, ReactNode } from 'react'
import cn from 'classnames'
import './ContentCard.scss'

type ContentCardProps = {
  title?: string
  description?: ReactNode
  action?: ReactNode
  className?: string
  children: ReactNode
}

const ContentCard: FC<ContentCardProps> = ({
  action,
  children,
  className,
  description,
  title,
}) => {
  return (
    <div className={cn('content-card', className)}>
      {(title || action || description) && (
        <div className='content-card__heading'>
          {(title || action) && (
            <div className='content-card__header'>
              {title && <h3 className='content-card__title'>{title}</h3>}
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
