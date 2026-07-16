import { createContext, FC, ReactNode, useContext } from 'react'
import ModalClose from 'components/modals/base/ModalClose'

// Shared header/body/footer slots + close context for Dialog and Drawer.
// titleId links the header title to the dialog via aria-labelledby.
export const DialogContext = createContext<{
  onClose: () => void
  titleId?: string
}>({
  onClose: () => undefined,
})

type SlotProps = {
  children: ReactNode
  className?: string
}

export const DialogHeader: FC<SlotProps> = ({ children, className }) => {
  const { onClose, titleId } = useContext(DialogContext)
  return (
    <div className={`dialog__header ${className ?? ''}`}>
      <h5 id={titleId} className='dialog__title'>
        {children}
      </h5>
      <ModalClose onClick={onClose} />
    </div>
  )
}

export const DialogBody: FC<SlotProps> = ({ children, className }) => (
  <div className={`dialog__body ${className ?? ''}`}>{children}</div>
)

export const DialogFooter: FC<SlotProps> = ({ children, className }) => (
  <div className={`dialog__footer ${className ?? ''}`}>{children}</div>
)
