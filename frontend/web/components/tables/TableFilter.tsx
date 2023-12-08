import React, { FC, useState } from 'react'
import InlineModal from 'components/InlineModal'
import { IonIcon } from '@ionic/react'
import { caretDown } from 'ionicons/icons'
import classNames from 'classnames'

type TableFilterType = {
  title: string
  className?: string
}

const TableFilter: FC<TableFilterType> = ({ className, title }) => {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Row className={classNames('cursor-pointer', className)}>
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
      <InlineModal
        title='Roles'
        isOpen={open}
        onClose={() => setOpen(false)}
        className='inline-modal--tags'
      >
        <div>Hi</div>
      </InlineModal>
    </>
  )
}

export default TableFilter
