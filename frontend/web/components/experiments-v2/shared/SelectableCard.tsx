import React from 'react'
import Icon, { IconName } from 'components/icons/Icon'
import './SelectableCard.scss'

type BadgeVariant = 'primary' | 'secondary' | 'guardrail'

type RoleOption<V extends string> = { label: string; value: V }

type SelectableCardProps<V extends string = string> = {
  selected: boolean
  onClick: () => void
  icon?: IconName
  title: string
  description: string
  badge?: { label: string; variant: BadgeVariant }
  /** Small info tags rendered under the title (e.g. measurement type). */
  tags?: string[]
  /** Segmented role picker rendered on the right when selected. Mutually
   *  exclusive with `badge`. */
  roleSelector?: {
    value: V
    options: RoleOption<V>[]
    onChange: (value: V) => void
  }
}

const SelectableCard = <V extends string = string>({
  badge,
  description,
  icon,
  onClick,
  roleSelector,
  selected,
  tags,
  title,
}: SelectableCardProps<V>) => {
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
        {roleSelector ? (
          <div className='selectable-card__role-group' role='radiogroup'>
            {roleSelector.options.map((opt) => (
              <button
                key={opt.value}
                type='button'
                className={`selectable-card__role-pill ${
                  roleSelector.value === opt.value
                    ? 'selectable-card__role-pill--active'
                    : ''
                }`}
                onClick={(e) => {
                  e.stopPropagation()
                  roleSelector.onChange(opt.value)
                }}
                aria-checked={roleSelector.value === opt.value}
                role='radio'
              >
                {opt.label}
              </button>
            ))}
          </div>
        ) : (
          badge && (
            <span
              className={`selectable-card__badge selectable-card__badge--${badge.variant}`}
            >
              {badge.label}
            </span>
          )
        )}
      </div>
    </div>
  )
}

SelectableCard.displayName = 'SelectableCard'
export default SelectableCard
