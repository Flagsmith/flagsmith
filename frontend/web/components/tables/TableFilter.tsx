import React, { FC, ReactNode, useState } from 'react'
import InlineModal from 'components/InlineModal'
import classNames from 'classnames'
import { ChevronDownIcon } from 'components/icons'

type TableFilterType = {
  title: string | ReactNode
  hideTitle?: boolean
  dropdownTitle?: ReactNode | string
  className?: string
  children: ReactNode
  'data-test'?: string
}

const TableFilter: FC<TableFilterType> = ({
  children,
  className,
  'data-test': dataTest,
  dropdownTitle,
  hideTitle,
  title,
}) => {
  const [open, setOpen] = useState(false)
  const toggle = function () {
    if (!open) {
      setOpen(true)
    }
  }
  return (
    <>
      <Row
        data-test={
          dataTest ||
          (typeof title === 'string'
            ? `table-filter-${title.toLowerCase()}`
            : undefined)
        }
        onClick={toggle}
        className={classNames(
          'cursor-pointer py-2 py-lg-0 user-select-none',
          className,
        )}
      >
        <span>{title} </span>
        <ChevronDownIcon className='ms-1' width={12} />
      </Row>
      {open && (
        <InlineModal
          hideClose
          title={hideTitle ? null : dropdownTitle || title}
          isOpen={open}
          onClose={() => {
            setTimeout(() => {
              setOpen(false)
            }, 10)
          }}
          containerClassName='px-0'
          className='inline-modal table-filter inline-modal--sm right'
        >
          {children}
        </InlineModal>
      )}
    </>
  )
}

export default TableFilter
