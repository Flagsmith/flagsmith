import React, { FC, ReactNode } from 'react'
import ModalClose from './ModalClose'
import ModalHR from 'components/modals/ModalHR'

type ModalHeaderType = {
  children: ReactNode
  onDismissClick: () => void
}

const ModalHeader: FC<ModalHeaderType> = ({ children, onDismissClick }) => {
  return (
    <>
      <div className='modal-header'>
        <h5 className='modal-title'>{children}</h5>
        <ModalClose onClick={onDismissClick} />
      </div>
      <ModalHR />
    </>
  )
}

export default ModalHeader
