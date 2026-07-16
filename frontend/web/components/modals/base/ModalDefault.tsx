import { Modal, ModalBody } from 'reactstrap'
import React, { FC, ReactNode, useEffect, useState } from 'react'
import ModalHeader from './ModalHeader'
import {
  interceptClose,
  registerModalTitleSetter,
  setInterceptClose,
  setModalTitle,
} from './modalController'

// interceptClose / setInterceptClose / setModalTitle now live in the controller
// so the in-tree manager can honour them. Re-exported here for existing imports
// (~15 call sites still import them from this path).
export { interceptClose, setInterceptClose, setModalTitle }

interface ModalDefault {
  title: ReactNode
  isOpen: boolean
  onDismiss?: () => void
  onClosed?: () => void
  toggle: () => void
  zIndex?: number
  children: ReactNode
  className?: string
  // reactstrap portal target. In-tree manager points this at #app so the modal
  // DOM lands inside the app root rather than <body>.
  container?: string
}

const ModalDefault: FC<ModalDefault> = ({
  children,
  className,
  container = 'app',
  isOpen,
  onClosed,
  onDismiss,
  title: _title,
  toggle,
  zIndex,
}) => {
  const [title, setTitle] = useState(_title)
  useEffect(() => {
    registerModalTitleSetter(setTitle)
    return () => registerModalTitleSetter(null)
  }, [])
  const onDismissClick = async () => {
    if (interceptClose) {
      const shouldClose = await interceptClose()
      if (!shouldClose) {
        return
      }
      setInterceptClose(null)
    }
    if (onDismiss) {
      onDismiss()
    }
    toggle()
  }
  return (
    <Modal
      className={
        !className?.includes('side-modal') ? 'modal-dialog-centered' : undefined
      }
      container={container}
      onClosed={onClosed}
      modalClassName={className}
      unmountOnClose
      isOpen={isOpen}
      toggle={onDismissClick}
      zIndex={zIndex}
    >
      <ModalHeader onDismissClick={onDismissClick}>{title}</ModalHeader>
      <ModalBody>{children}</ModalBody>
    </Modal>
  )
}

export default ModalDefault
