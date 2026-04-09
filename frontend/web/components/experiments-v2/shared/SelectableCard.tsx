import React, { FC } from 'react'
import Icon, { IconName } from 'components/icons/Icon'
import './SelectableCard.scss'

type BadgeVariant = 'primary' | 'secondary'

type SelectableCardProps = {
  selected: boolean
  onClick: () => void
  icon?: IconName
  title: string
  description: string
  badge?: { label: string; variant: BadgeVariant }
}

const SelectableCard: FC<SelectableCardProps> = ({
  badge,
  description,
  icon,
  onClick,
  selected,
  title,
}) => {
  return (
    <button
      className={`selectable-card ${
        selected ? 'selectable-card--selected' : ''
      }`}
      onClick={onClick}
      type='button'
    >
      <div className='selectable-card__content'>
        {icon && <Icon name={icon} width={20} />}
        <span className='selectable-card__title'>{title}</span>
        <span className='selectable-card__description'>{description}</span>
      </div>
      {badge && (
        <span
          className={`selectable-card__badge selectable-card__badge--${badge.variant}`}
        >
          {badge.label}
        </span>
      )}
    </button>
  )
}

SelectableCard.displayName = 'SelectableCard'
export default SelectableCard
