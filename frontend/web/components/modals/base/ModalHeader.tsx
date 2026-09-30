import React, { FC, ReactNode } from 'react'
import ModalClose from './ModalClose'
import ModalHR from 'components/modals/ModalHR'
import Text from 'components/base/Text'

type ModalHeaderType = {
  children: ReactNode
  onDismissClick: () => void
}

const ModalHeader: FC<ModalHeaderType> = ({ children, onDismissClick }) => {
  return (
    <>
      <div className='modal-header'>
        <Text variant='h5' level={2} className='modal-title'>
          {children}
        </Text>
        <ModalClose onClick={onDismissClick} />
      </div>
      <ModalHR />
    </>
  )
}

export default ModalHeader
