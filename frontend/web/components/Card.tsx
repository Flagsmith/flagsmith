import { FC, ReactNode } from 'react'
import classNames from 'classnames'

type CardType = {
  children: ReactNode
  className?: string
  contentClassName?: string
}

const Card: FC<CardType> = ({ children, className, contentClassName }) => {
  return (
    <div className={`rounded-3 panel panel-default ${className || ''}`}>
      <div className={classNames('panel-content p-4', contentClassName)}>
        {children}
      </div>
    </div>
  )
}

export default Card
