import React, { FC, ReactNode } from 'react'
import Icon from 'components/Icon'
import classNames from 'classnames'

type TableFilterItemType = {
  isActive?: boolean
  subtitle?: string
  title: string | ReactNode
  onClick: () => void
  'data-test'?: string
}

const TableFilterItem: FC<TableFilterItemType> = ({
  isActive,
  onClick,
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
            className={classNames('text-body', { 'opacity-0': !isActive })}
            name={'checkmark'}
          />
        </div>
      </Row>
    </a>
  )
}

export default TableFilterItem
