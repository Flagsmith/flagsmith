import { FC, ReactNode } from 'react'
import Dialog from 'components/base/Dialog'
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
  <Dialog
    open={isOpen}
    onClose={onClose}
    size='full'
    className={`centered-modal ${className ?? ''}`}
  >
    <Dialog.Header>{title}</Dialog.Header>
    <Dialog.Body>{children}</Dialog.Body>
  </Dialog>
)

export default CenteredModal
