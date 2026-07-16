import { FC, ReactNode, useId } from 'react'
import { useNativeDialog } from './useNativeDialog'
import {
  DialogBody,
  DialogContext,
  DialogFooter,
  DialogHeader,
} from './DialogSlots'
import './Dialog.scss'

export type DialogSize = 'sm' | 'md' | 'lg' | 'full'

export type DialogProps = {
  open: boolean
  onClose: () => void
  size?: DialogSize
  className?: string
  children: ReactNode
}

const DialogRoot: FC<DialogProps> = ({
  children,
  className,
  onClose,
  open,
  size = 'md',
}) => {
  const { onCancel, onClick, ref } = useNativeDialog(open, onClose)
  const titleId = useId()
  return (
    <DialogContext.Provider value={{ onClose, titleId }}>
      <dialog
        ref={ref}
        aria-labelledby={titleId}
        className={`dialog dialog--${size} ${className ?? ''}`}
        onCancel={onCancel}
        onClick={onClick}
      >
        <div className='dialog__panel'>{children}</div>
      </dialog>
    </DialogContext.Provider>
  )
}

const Dialog = Object.assign(DialogRoot, {
  Body: DialogBody,
  Footer: DialogFooter,
  Header: DialogHeader,
})

export default Dialog
