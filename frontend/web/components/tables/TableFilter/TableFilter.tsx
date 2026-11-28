import React, { FC, ReactNode } from 'react'
import classNames from 'classnames'
import Popover from 'components/base/Popover'
import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import { useBreakpoint } from 'common/hooks/useBreakpoint'
import './TableFilter.scss'

type TableFilterType = {
  title: string | ReactNode
  // Names the filter when the title isn't plain text (it has a count)
  label?: string
  className?: string
  children: ReactNode | ((close: () => void) => ReactNode)
}

const TableFilter: FC<TableFilterType> = ({
  children,
  className,
  label,
  title,
}) => {
  // Popover opens as a sheet on the same breakpoint, where rows get larger
  const asSheet = useBreakpoint('isPhone')
  return (
    <Popover
      aria-label={label ?? (typeof title === 'string' ? title : 'Filter')}
      placement='bottom-end'
      // Width for the anchored panel; the phone sheet is full width
      className='table-filter__panel'
      renderTrigger={(props) => (
        <BareButton
          {...props}
          className={classNames(
            'd-flex align-items-center py-2 py-lg-0 user-select-none',
            className,
          )}
        >
          <span>{title} </span>
          <Icon name='chevron-down' width={16} />
        </BareButton>
      )}
    >
      {(close) => (
        <div
          className={classNames('table-filter__content', {
            'table-filter__content--sheet': asSheet,
          })}
        >
          {typeof children === 'function' ? children(close) : children}
        </div>
      )}
    </Popover>
  )
}

export default TableFilter
