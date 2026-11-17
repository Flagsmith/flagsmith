import React, { FC, ReactNode } from 'react'
import { IonIcon } from '@ionic/react'
import { caretDown } from 'ionicons/icons'
import classNames from 'classnames'
import Popover from 'components/base/Popover'
import BareButton from 'components/base/forms/BareButton'

type TableFilterType = {
  title: string | ReactNode
  // Names the filter when the title isn't plain text (it has a count)
  label?: string
  hideTitle?: boolean
  dropdownTitle?: ReactNode | string
  className?: string
  size?: 'sm' | 'lg'
  children: ReactNode | ((close: () => void) => ReactNode)
  'data-test'?: string
}

const TableFilter: FC<TableFilterType> = ({
  children,
  className,
  'data-test': dataTest,
  dropdownTitle,
  hideTitle,
  label,
  size = 'sm',
  title,
}) => (
  <Popover
    aria-label={label ?? (typeof title === 'string' ? title : 'Filter')}
    placement='bottom-end'
    // Width for the anchored panel; the phone sheet is full width
    className={`inline-modal--${size}`}
    renderTrigger={(props) => (
      <BareButton
        {...props}
        data-test={
          dataTest ||
          (typeof title === 'string'
            ? `table-filter-${title.toLowerCase()}`
            : undefined)
        }
        className={classNames(
          'd-flex align-items-center py-2 py-lg-0 user-select-none',
          className,
        )}
      >
        <span>{title} </span>
        <IonIcon
          style={{
            fontSize: 11,
            marginLeft: 2,
            marginTop: 4,
          }}
          icon={caretDown}
        />
      </BareButton>
    )}
  >
    {(close) => (
      <>
        {!hideTitle && (
          <div className='inline-modal__title px-3 py-2'>
            {dropdownTitle || title}
          </div>
        )}
        {typeof children === 'function' ? children(close) : children}
      </>
    )}
  </Popover>
)

export default TableFilter
