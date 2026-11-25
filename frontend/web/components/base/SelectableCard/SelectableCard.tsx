import React, { FC, ReactNode } from 'react'
import cn from 'classnames'
import BareButton from 'components/base/forms/BareButton'
import './SelectableCard.scss'

type BadgeVariant = 'primary' | 'secondary'

type SelectableCardProps = {
  // Selection state. Omit for a card that acts on click without a chosen state
  // (e.g. a card that navigates).
  selected?: boolean
  onClick: () => void
  icon?: ReactNode
  title: ReactNode
  description: ReactNode
  badge?: { label: string; variant: BadgeVariant }
  tags?: string[]
  disabled?: boolean
  className?: string
  // Extra content below the description (e.g. an illustrative preview).
  children?: ReactNode
  // Content inside the card but outside its button (e.g. a form control).
  footer?: ReactNode
}

const SelectableCard: FC<SelectableCardProps> = ({
  badge,
  children,
  className,
  description,
  disabled,
  footer,
  icon,
  onClick,
  selected,
  tags,
  title,
}) => {
  return (
    <div
      className={cn(
        'selectable-card',
        {
          'selectable-card--disabled': disabled,
          'selectable-card--selected': selected,
        },
        className,
      )}
    >
      <BareButton
        className='selectable-card__body'
        onClick={onClick}
        disabled={disabled}
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
          {children}
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
      </BareButton>
      {footer && (
        <div className='px-3 pb-3' inert={disabled}>
          {footer}
        </div>
      )}
    </div>
  )
}

SelectableCard.displayName = 'SelectableCard'
export default SelectableCard
