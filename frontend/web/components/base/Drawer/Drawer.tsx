import { FC, ReactNode } from 'react'
import { useNativeDialog } from 'components/base/Dialog/useNativeDialog'
import {
  DialogBody,
  DialogContext,
  DialogFooter,
  DialogHeader,
} from 'components/base/Dialog/DialogSlots'
import 'components/base/Dialog/Dialog.scss'
import './Drawer.scss'

export type DrawerWidth = 'default' | 'narrow'

export type DrawerProps = {
  open: boolean
  onClose: () => void
  width?: DrawerWidth
  className?: string
  children: ReactNode
}

const DrawerRoot: FC<DrawerProps> = ({
  children,
  className,
  onClose,
  open,
  width = 'default',
}) => {
  const { onCancel, onClick, ref } = useNativeDialog(open, onClose)
  return (
    <DialogContext.Provider value={{ onClose }}>
      <dialog
        ref={ref}
        className={`drawer drawer--${width} ${className ?? ''}`}
        onCancel={onCancel}
        onClick={onClick}
      >
        <div className='dialog__panel drawer__panel'>{children}</div>
      </dialog>
    </DialogContext.Provider>
  )
}

// Drawer shares Dialog's header/body/footer slots.
const Drawer = Object.assign(DrawerRoot, {
  Body: DialogBody,
  Footer: DialogFooter,
  Header: DialogHeader,
})

export default Drawer
