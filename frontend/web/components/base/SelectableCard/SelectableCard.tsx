import React, { FC, ReactNode } from 'react'
import './SelectableCard.scss'

type BadgeVariant = 'primary' | 'secondary'

type SelectableCardProps = {
  selected: boolean
  onClick: () => void
  icon?: ReactNode
  title: string
  description: string
  badge?: { label: string; variant: BadgeVariant }
  tags?: string[]
  disabled?: boolean
}

const SelectableCard: FC<SelectableCardProps> = ({
  badge,
  description,
  disabled,
  icon,
  onClick,
  selected,
  tags,
  title,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onClick()
    }
  }

  return (
    <div
      className={`selectable-card${
        selected ? ' selectable-card--selected' : ''
      }${disabled ? ' selectable-card--disabled' : ''}`}
      onClick={disabled ? undefined : onClick}
      onKeyDown={disabled ? undefined : handleKeyDown}
      role='button'
      tabIndex={disabled ? -1 : 0}
    >
      <div className='selectable-card__content'>
        {icon && <div className='selectable-card__icon'>{icon}</div>}
        <span className='selectable-card__title'>{title}</span>
        <span className='selectable-card__description'>{description}</span>
        {!!tags?.length && (
          <div className='selectable-card__tags'>
            {tags.map((tag) => (
              <span key={tag} className='selectable-card__tag'>
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
      {badge && (
        <div className='selectable-card__aside'>
          <span
            className={`selectable-card__badge selectable-card__badge--${badge.variant}`}
          >
            {badge.label}
          </span>
        </div>
      )}
    </div>
  )
}

SelectableCard.displayName = 'SelectableCard'
export default SelectableCard
