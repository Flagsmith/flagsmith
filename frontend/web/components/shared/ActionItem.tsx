import { FC, ReactNode } from 'react'
import classNames from 'classnames'

interface ActionRowProps {
  handleActionClick: () => void
  index: number
  entity: 'feature' | 'segment'
  icon: ReactNode
  label: string
  disabled?: boolean
  disableE2E?: boolean
  action: 'remove' | 'copy' | 'audit' | 'history' | 'clone'
}

const ActionItem: FC<ActionRowProps> = ({
  action,
  disableE2E,
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
      data-test={!disableE2E ? `${entity}-${action}-${index}` : undefined}
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
