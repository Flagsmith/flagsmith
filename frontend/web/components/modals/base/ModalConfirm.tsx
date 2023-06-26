import { Modal, ModalBody, ModalFooter } from 'reactstrap'
import Button from 'components/base/forms/Button'
import { FC, ReactNode } from 'react'

interface Confirm {
  disabled?: boolean
  disabledYes?: boolean
  isDanger?: boolean
  isOpen: boolean
  noText?: string
  onNo?: () => void
  onYes?: () => void
  title: ReactNode
  toggle: () => void
  yesText?: string
  zIndex?: number
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
  zIndex,
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
      zIndex={zIndex}
      isOpen={isOpen}
      toggle={no}
    >
      <div className='modal-header'>
        <h5 className='modal-title'>{title}</h5>
        <span onClick={no} className='icon close ion-md-close' />
      </div>
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
