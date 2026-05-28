import { FC, ReactNode } from 'react'
import cn from 'classnames'
import './ContentCard.scss'

type ContentCardProps = {
  title?: string
  action?: ReactNode
  className?: string
  children: ReactNode
}

const ContentCard: FC<ContentCardProps> = ({
  action,
  children,
  className,
  title,
}) => {
  return (
    <div className={cn('content-card', className)}>
      {(title || action) && (
        <div className='content-card__header'>
          {title && <h3 className='content-card__title'>{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  )
}

export default ContentCard
