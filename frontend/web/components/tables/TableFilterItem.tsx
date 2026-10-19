import React, { FC, ReactNode } from 'react'
import Icon from 'components/icons/Icon'
import classNames from 'classnames'
import BareButton from 'components/base/forms/BareButton'

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
    <BareButton {...rest} onClick={onClick} className='table-filter-item w-100'>
      <Row space className='px-3 no-wrap overflow-hidden py-2'>
        <div className={'overflow-ellipsis'}>
          {title}
          {subtitle && <div className='text-muted fw-normal'>{subtitle}</div>}
        </div>
        <div>
          <Icon
            className={classNames('text-default', { 'opacity-0': !isActive })}
            name={'checkmark'}
          />
        </div>
      </Row>
    </BareButton>
  )
}

export default TableFilterItem
