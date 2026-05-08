import React from 'react'
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
  /** Small info tags rendered under the title (e.g. measurement type). */
  tags?: string[]
  /** Primary-metric toggle rendered when the card is selected. Mutually
   *  exclusive with `badge`. */
  primaryToggle?: {
    isPrimary: boolean
    onSetPrimary: () => void
  }
}

const SelectableCard: React.FC<SelectableCardProps> = ({
  badge,
  description,
  icon,
  onClick,
  primaryToggle,
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
      className={`selectable-card ${
        selected ? 'selectable-card--selected' : ''
      }`}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      role='button'
      tabIndex={0}
    >
      <div className='selectable-card__content'>
        {icon && <Icon name={icon} width={20} />}
        <span className='selectable-card__title'>{title}</span>
        <span className='selectable-card__description'>{description}</span>
        {tags && tags.length > 0 && (
          <div className='selectable-card__tags'>
            {tags.map((t) => (
              <span key={t} className='selectable-card__tag'>
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className='selectable-card__aside'>
        {primaryToggle?.isPrimary && (
          <span className='selectable-card__badge selectable-card__badge--primary'>
            Primary
          </span>
        )}
        {primaryToggle && !primaryToggle.isPrimary && (
          <button
            type='button'
            className='selectable-card__set-primary'
            onClick={(e) => {
              e.stopPropagation()
              primaryToggle.onSetPrimary()
            }}
          >
            Set as primary
          </button>
        )}
        {!primaryToggle && badge && (
          <span
            className={`selectable-card__badge selectable-card__badge--${badge.variant}`}
          >
            {badge.label}
          </span>
        )}
      </div>
    </div>
  )
}

SelectableCard.displayName = 'SelectableCard'
export default SelectableCard
