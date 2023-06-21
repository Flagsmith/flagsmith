import { Modal, ModalBody, ModalFooter, ModalHeader } from 'reactstrap'
import Button from 'components/base/forms/Button'
import { FC, ReactNode } from 'react'

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
    <Modal unmountOnClose isOpen={isOpen} toggle={no}>
      <ModalHeader toggle={no}>{title}</ModalHeader>
      <ModalBody>{children}</ModalBody>
      <ModalFooter>
        <Button
          theme='secondary'
          id='confirm-btn-no'
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
            iconRight='plus'
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
