import React, { FC, ReactNode } from 'react'
import ModalClose from './ModalClose' // we need this to make JSX compile

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
      <hr className='py-0 my-0' />
    </>
  )
}

export default ModalHeader
