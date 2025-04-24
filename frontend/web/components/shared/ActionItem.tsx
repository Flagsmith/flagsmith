import { FC, ReactNode } from 'react'
import classNames from 'classnames'

interface ActionRowProps {
  handleActionClick: () => void
  index: number
  entity: 'feature' | 'segment'
  icon: ReactNode
  label: string
  disabled?: boolean
}

const ActionItem: FC<ActionRowProps> = ({
  disabled,
  entity,
  handleActionClick,
  icon,
  index,
  label,
}) => {
  return (
    <div
      className={classNames('feature-action__item', {
        'feature-action__item_disabled': disabled,
      })}
      data-test={`${entity}-action-${index}`}
      onClick={(e) => {
        if (disabled) {
          return
        }
        e.stopPropagation()
        handleActionClick()
      }}
    >
      {!!icon && icon}
      <span>{label}</span>
    </div>
  )
}

export default ActionItem
