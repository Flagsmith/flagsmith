import React, { FC, ReactNode, useState } from 'react'
import InlineModal from 'components/InlineModal'
import { IonIcon } from '@ionic/react'
import { caretDown } from 'ionicons/icons'
import classNames from 'classnames'

type TableFilterType = {
  title: string
  hideTitle?: boolean
  dropdownTitle?: ReactNode | string
  className?: string
  children: ReactNode
}

const TableFilter: FC<TableFilterType> = ({
  children,
  className,
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
