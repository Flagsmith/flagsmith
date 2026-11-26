import React, { FC, ReactNode } from 'react'
import Icon from 'components/icons/Icon'
import BareButton from 'components/base/forms/BareButton'
import classNames from 'classnames'
import { SortOrder } from 'common/types/requests'
import './TableFilterItem.scss'

type TableFilterItemType = {
  isActive?: boolean
  // For sort options: the active one shows its direction instead of a tick
  sortOrder?: SortOrder
  subtitle?: string
  title: string | ReactNode
  onClick: () => void
}

const markerIcon = (sortOrder?: SortOrder) => {
  if (!sortOrder) return 'checkmark'
  return sortOrder === SortOrder.ASC ? 'chevron-up' : 'chevron-down'
}

const TableFilterItem: FC<TableFilterItemType> = ({
  isActive,
  onClick,
  sortOrder,
  subtitle,
  title,
  ...rest
}) => {
  return (
    <BareButton
      {...rest}
      // Toggled filter or the active sort option
      aria-pressed={!!isActive}
      onClick={onClick}
      className='table-filter-item'
    >
      <span className='d-flex align-items-center justify-content-between gap-2 px-3 py-2 overflow-hidden'>
        <span className='overflow-ellipsis'>
          {title}
          {subtitle && (
            <span className='d-block text-muted fw-normal'>{subtitle}</span>
          )}
        </span>
        <Icon
          className={classNames('text-default flex-shrink-0', {
            'opacity-0': !isActive,
          })}
          name={markerIcon(sortOrder)}
        />
      </span>
    </BareButton>
  )
}

export default TableFilterItem
