import {
  createContext,
  FC,
  MouseEvent,
  ReactNode,
  SyntheticEvent,
  useContext,
  useEffect,
  useRef,
} from 'react'
import ModalClose from 'components/modals/base/ModalClose'
import './Dialog.scss'

export type DialogSize = 'sm' | 'md' | 'lg' | 'full' | 'side'

export type DialogProps = {
  open: boolean
  onClose: () => void
  size?: DialogSize
  className?: string
  children: ReactNode
}

type SlotProps = {
  children: ReactNode
  className?: string
}

const DialogContext = createContext<{ onClose: () => void }>({
  onClose: () => undefined,
})

// Ref-counted body class so the app's `.modal-open` rules (scroll lock, hiding
// the support chat) still fire and survive stacked dialogs.
let openDialogs = 0
const useBodyModalOpen = (open: boolean) => {
  useEffect(() => {
    if (!open) return
    openDialogs += 1
    document.body.classList.add('modal-open')
    return () => {
      openDialogs -= 1
      if (openDialogs <= 0) {
        openDialogs = 0
        document.body.classList.remove('modal-open')
      }
    }
  }, [open])
}

const DialogRoot: FC<DialogProps> = ({
  children,
  className,
  onClose,
  open,
  size = 'md',
}) => {
  const ref = useRef<HTMLDialogElement>(null)
  useBodyModalOpen(open)

  // Drive the native dialog imperatively. showModal() promotes it to the top
  // layer, so there is no z-index handling and no portal target to configure.
  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <DialogContext.Provider value={{ onClose }}>
      <dialog
        ref={ref}
        className={`dialog dialog--${size} ${className ?? ''}`}
        onCancel={(e: SyntheticEvent<HTMLDialogElement>) => {
          // Esc: run our onClose rather than the browser's immediate close.
          e.preventDefault()
          onClose()
        }}
        onClick={(e: MouseEvent<HTMLDialogElement>) => {
          // A click landing on the dialog element itself is a backdrop click.
          if (e.target === ref.current) onClose()
        }}
      >
        <div className='dialog__panel'>{children}</div>
      </dialog>
    </DialogContext.Provider>
  )
}

const DialogHeader: FC<SlotProps> = ({ children, className }) => {
  const { onClose } = useContext(DialogContext)
  return (
    <div className={`dialog__header ${className ?? ''}`}>
      <h5 className='dialog__title'>{children}</h5>
      <ModalClose onClick={onClose} />
    </div>
  )
}

const DialogBody: FC<SlotProps> = ({ children, className }) => (
  <div className={`dialog__body ${className ?? ''}`}>{children}</div>
)

const DialogFooter: FC<SlotProps> = ({ children, className }) => (
  <div className={`dialog__footer ${className ?? ''}`}>{children}</div>
)

const Dialog = Object.assign(DialogRoot, {
  Body: DialogBody,
  Footer: DialogFooter,
  Header: DialogHeader,
})

export default Dialog
