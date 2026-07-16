import { FC, ReactNode } from 'react'
import Button from 'components/base/forms/Button'
import Dialog from './Dialog'

export type ConfirmDialogProps = {
  open: boolean
  title: ReactNode
  children: ReactNode
  onYes: () => void
  onNo: () => void
  destructive?: boolean
  yesText?: string
  noText?: string
}

// Small Dialog preset for yes/no confirmations. Backs the imperative
// openConfirm and is usable declaratively for new code.
const ConfirmDialog: FC<ConfirmDialogProps> = ({
  children,
  destructive,
  noText = 'Cancel',
  onNo,
  onYes,
  open,
  title,
  yesText = 'OK',
}) => (
  <Dialog open={open} size='sm' onClose={onNo}>
    <Dialog.Header>{title}</Dialog.Header>
    <Dialog.Body>{children}</Dialog.Body>
    <Dialog.Footer>
      <Button theme='secondary' id='confirm-btn-no' onClick={onNo}>
        {noText}
      </Button>
      <Button
        theme={destructive ? 'danger' : 'primary'}
        id='confirm-btn-yes'
        onClick={onYes}
      >
        {yesText}
      </Button>
    </Dialog.Footer>
  </Dialog>
)

export default ConfirmDialog
