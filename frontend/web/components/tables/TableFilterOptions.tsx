import React, { FC, ReactNode, useState } from 'react'
import InlineModal from 'components/InlineModal'
import { IonIcon } from '@ionic/react'
import { caretDown } from 'ionicons/icons'
import classNames from 'classnames'
import TableFilterItem from './TableFilterItem'

type TableFilterType = {
  title: string
  dropdownTitle?: ReactNode | string
  className?: string
  options: { label: string; value: string }[]
  onChange: (value: string) => void
  value: string
}

const TableFilter: FC<TableFilterType> = ({
  className,
  dropdownTitle,
  onChange,
  options,
  title,
  value,
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
        onClick={toggle}
        className={classNames('cursor-pointer user-select-none', className)}
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
      </Row>
      {open && (
        <InlineModal
          hideClose
          title={null}
          isOpen={open}
          onClose={() => {
            setTimeout(() => {
              setOpen(false)
            }, 10)
          }}
          containerClassName='px-0'
          className='inline-modal table-filter inline-modal--sm right'
        >
          {options.map((v) => (
            <TableFilterItem
              key={v.value}
              title={v.label}
              onClick={() => {
                setOpen(false)
                onChange(v.value)
              }}
              isActive={value === v.value}
            />
          ))}
        </InlineModal>
      )}
    </>
  )
}

export default TableFilter
