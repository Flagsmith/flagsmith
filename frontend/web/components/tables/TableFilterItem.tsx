import React, { FC, ReactNode } from 'react'
import Icon from 'components/Icon'
import classNames from 'classnames'

type TableFilterItemType = {
  isActive?: boolean
  title: string | ReactNode
  onClick: () => void
}

const TableFilterItem: FC<TableFilterItemType> = ({
  isActive,
  onClick,
  title,
}) => {
  return (
    <a href={'#'} onClick={onClick} className='popover-bt__list-item'>
      <Row space className='px-3 no-wrap overflow-hidden py-2'>
        {title}
        <div>
          <Icon
            className={classNames('text-body', { 'opacity-0': !isActive })}
            name={'checkmark'}
          />
        </div>
      </Row>
    </a>
  )
}

export default TableFilterItem
