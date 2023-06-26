import { Modal, ModalBody, ModalFooter } from 'reactstrap'
import Button from 'components/base/forms/Button'
import React, { FC, ReactNode } from 'react'
import ModalHeader from './ModalHeader'

interface Confirm {
  title: ReactNode
  isOpen: boolean
  isDanger?: boolean
  onYes?: () => void
  onNo?: () => void
  noText?: string
  disabled?: boolean
  disabledYes?: boolean
  yesText?: string
  toggle: () => void
}

const Confirm: FC<Confirm> = ({
  children,
  disabled,
  disabledYes,
  isDanger,
  isOpen,
  noText = 'Cancel',
  onNo,
  onYes,
  title,
  toggle,
  yesText = 'OK',
}) => {
  const no = () => {
    onNo?.()
    toggle()
  }
  const yes = () => {
    onYes?.()
    toggle()
  }

  return (
    <Modal
      className='modal-dialog-centered'
      unmountOnClose
      isOpen={isOpen}
      toggle={no}
    >
      <ModalHeader onDismissClick={no}>{title}</ModalHeader>
      <ModalBody className='text-body'>{children}</ModalBody>
      <hr className='my-0 py-0' />
      <ModalFooter>
        <Button
          theme='secondary'
          id='confirm-btn-no'
          className='mr-2'
          disabled={disabled}
          onClick={no}
        >
          {noText}
        </Button>
        {isDanger ? (
          <Button
            theme='danger'
            id='confirm-btn-yes'
            disabled={disabled || disabledYes}
            iconRight='fas fa-trash'
            onClick={yes}
          >
            {yesText}
          </Button>
        ) : (
          <Button
            id='confirm-btn-yes'
            disabled={disabled || disabledYes}
            onClick={yes}
          >
            {yesText}
          </Button>
        )}{' '}
      </ModalFooter>
    </Modal>
  )
}

export default Confirm
