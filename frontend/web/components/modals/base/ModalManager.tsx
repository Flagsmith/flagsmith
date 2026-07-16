import { FC, ReactNode, useEffect, useState, useSyncExternalStore } from 'react'
import Dialog, { ConfirmDialog, DialogSize } from 'components/base/Dialog'
import Drawer from 'components/base/Drawer'
import {
  clearConfirm,
  ConfirmEntry,
  getModalState,
  ModalEntry,
  ModalState,
  registerModalTitleSetter,
  requestCloseModal,
  subscribeModals,
} from './modalController'

// PoC (spike): renders the imperative modal stack with the DS Dialog (native
// <dialog>, top layer). Mounted once from App.js under the store <Provider>.
// Close is owned by the controller (stable closeModal/closeModal2 globals), so
// dismiss just routes through requestCloseModal by stack index.

// Map the legacy openModal className to a Dialog size.
const sizeFor = (className?: string): DialogSize => {
  if (!className) return 'md'
  if (className.includes('modal-full-screen')) return 'full'
  if (className.includes('modal-lg')) return 'lg'
  if (className.includes('modal-sm')) return 'sm'
  return 'md'
}

const ModalSlot: FC<{ entry: ModalEntry; index: number }> = ({
  entry,
  index,
}) => {
  const [title, setTitle] = useState<ReactNode>(entry.title)

  // The main modal (index 0) owns the dynamic-title setter, matching the old
  // ModalDefault behaviour.
  useEffect(() => {
    if (index !== 0) return undefined
    registerModalTitleSetter(setTitle)
    return () => registerModalTitleSetter(null)
  }, [index])

  const onClose = () => requestCloseModal(index)

  // Legacy side-modal maps to the Drawer; everything else is a centred Dialog.
  if (entry.className?.includes('side-modal')) {
    return (
      <Drawer
        open
        width={entry.className.includes('narrow') ? 'narrow' : 'default'}
        className={entry.className}
        onClose={onClose}
      >
        <Drawer.Header>{title}</Drawer.Header>
        <Drawer.Body>{entry.body}</Drawer.Body>
      </Drawer>
    )
  }

  return (
    <Dialog
      open
      size={sizeFor(entry.className)}
      className={entry.className}
      onClose={onClose}
    >
      <Dialog.Header>{title}</Dialog.Header>
      <Dialog.Body>{entry.body}</Dialog.Body>
    </Dialog>
  )
}

const ConfirmSlot: FC<{ entry: ConfirmEntry }> = ({ entry }) => {
  const no = () => {
    entry.onNo?.()
    clearConfirm()
  }
  const yes = () => {
    entry.onYes?.()
    clearConfirm()
  }
  return (
    <ConfirmDialog
      open
      title={entry.title}
      destructive={entry.destructive}
      yesText={entry.yesText}
      noText={entry.noText}
      onYes={yes}
      onNo={no}
    >
      {entry.body}
    </ConfirmDialog>
  )
}

const ModalManager: FC = () => {
  const state: ModalState = useSyncExternalStore(subscribeModals, getModalState)
  return (
    <>
      {state.modals.map((entry, index) => (
        <ModalSlot key={entry.key} entry={entry} index={index} />
      ))}
      {state.confirm && (
        <ConfirmSlot key={state.confirm.key} entry={state.confirm} />
      )}
    </>
  )
}

export default ModalManager
