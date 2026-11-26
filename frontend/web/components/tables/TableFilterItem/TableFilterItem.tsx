import React, { FC, ReactNode } from 'react'
import Icon from 'components/icons/Icon'
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
  'data-test'?: string
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
    <a
      {...rest}
      href={'#'}
      onClick={(e) => {
        e.preventDefault()
        onClick()
      }}
      className='table-filter-item'
    >
      <Row space className='px-3 no-wrap overflow-hidden py-2'>
        <div className={'overflow-ellipsis'}>
          {title}
          {subtitle && <div className='text-muted fw-normal'>{subtitle}</div>}
        </div>
        <div>
          <Icon
            className={classNames('text-default', { 'opacity-0': !isActive })}
            name={markerIcon(sortOrder)}
          />
        </div>
      </Row>
    </a>
  )
}

export default TableFilterItem
