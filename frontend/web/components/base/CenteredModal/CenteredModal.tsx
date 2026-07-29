import { FC, ReactNode } from 'react'
import { Modal, ModalBody } from 'reactstrap'
import ModalHeader from 'components/modals/base/ModalHeader'
import './CenteredModal.scss'

type CenteredModalProps = {
  isOpen: boolean
  title: ReactNode
  onClose: () => void
  children: ReactNode
  className?: string
}

const CenteredModal: FC<CenteredModalProps> = ({
  children,
  className,
  isOpen,
  onClose,
  title,
}) => (
  <Modal
    className={`modal-dialog-centered centered-modal ${className ?? ''}`}
    isOpen={isOpen}
    toggle={onClose}
    unmountOnClose
  >
    <ModalHeader onDismissClick={onClose}>{title}</ModalHeader>
    <ModalBody>{children}</ModalBody>
  </Modal>
)

export default CenteredModal
