import { Modal, ModalBody } from 'reactstrap'
import React, { FC, ReactNode, useState } from 'react'
import ModalHeader from './ModalHeader'

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

export let interceptClose: (() => Promise<boolean>) | null = null
export const setInterceptClose = (promise: (() => Promise<any>) | null) => {
  interceptClose = promise
}

let cb: ((title: ReactNode) => void) | undefined
export const setModalTitle = (title: string) => {
  cb?.(title)
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
  cb = setTitle
  const onDismissClick = async () => {
    if (interceptClose) {
      const shouldClose = await interceptClose()
      if (!shouldClose) {
        return
      }
      interceptClose = null
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
